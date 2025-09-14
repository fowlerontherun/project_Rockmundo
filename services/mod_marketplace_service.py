"""Service layer for publishing and purchasing mods from the marketplace."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from backend.services.economy_service import EconomyService
from backend.services.storage_service import get_storage_backend
from storage.base import StorageBackend

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class ModMarketplaceError(Exception):
    pass


class ModMarketplaceService:
    def __init__(
        self,
        db_path: Optional[str] = None,
        storage: Optional[StorageBackend] = None,
        economy: Optional[EconomyService] = None,
    ) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.storage = storage or get_storage_backend()
        self.economy = economy or EconomyService(db_path=self.db_path)

    # --------------------------- schema ---------------------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS mods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    file_key TEXT NOT NULL,
                    price_cents INTEGER NOT NULL,
                    rating_sum INTEGER NOT NULL DEFAULT 0,
                    rating_count INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS mod_ownership (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mod_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(mod_id, user_id)
                )
                """
            )
            conn.commit()

    # --------------------------- helpers ---------------------------
    def _get_mod(self, cur: sqlite3.Cursor, mod_id: int) -> Dict:
        cur.execute("SELECT * FROM mods WHERE id = ?", (mod_id,))
        row = cur.fetchone()
        if not row:
            raise ModMarketplaceError("Mod not found")
        columns = [d[0] for d in cur.description]
        return dict(zip(columns, row))

    # --------------------------- publishing ---------------------------
    def publish_mod(
        self,
        author_id: int,
        name: str,
        description: str,
        price_cents: int,
        file_bytes: bytes,
        content_type: str = "application/octet-stream",
    ) -> int:
        """Store the mod file and create a pending marketplace entry."""

        key = f"mods/{uuid4().hex}.mod"
        obj = self.storage.upload_bytes(file_bytes, key, content_type=content_type)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO mods (author_id, name, description, file_key, price_cents)
                VALUES (?, ?, ?, ?, ?)
                """,
                (author_id, name, description, obj.key, price_cents),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    # --------------------------- reviews ---------------------------
    def list_pending_mods(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM mods WHERE status = 'pending' ORDER BY created_at ASC")
            return [dict(r) for r in cur.fetchall()]

    def approve_mod(self, mod_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE mods SET status = 'approved' WHERE id = ?", (mod_id,))
            if cur.rowcount == 0:
                raise ModMarketplaceError("Mod not found")
            conn.commit()

    # --------------------------- purchasing ---------------------------
    def download_mod(self, user_id: int, mod_id: int) -> str:
        """Purchase (transfer funds) and return a download URL."""

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            mod = self._get_mod(cur, mod_id)
            if mod["status"] != "approved":
                raise ModMarketplaceError("Mod not approved")
            self.economy.transfer(user_id, mod["author_id"], mod["price_cents"])
            cur.execute(
                "INSERT OR IGNORE INTO mod_ownership (mod_id, user_id) VALUES (?, ?)",
                (mod_id, user_id),
            )
            conn.commit()
        return self.storage.url_for(mod["file_key"])

    # --------------------------- ratings ---------------------------
    def rate_mod(self, user_id: int, mod_id: int, rating: int) -> None:
        if not (1 <= rating <= 5):
            raise ModMarketplaceError("rating must be between 1 and 5")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            # ensure mod exists
            self._get_mod(cur, mod_id)
            cur.execute(
                "UPDATE mods SET rating_sum = rating_sum + ?, rating_count = rating_count + 1 WHERE id = ?",
                (rating, mod_id),
            )
            conn.commit()
