"""Service layer for managing venues.

The service stores venue information in the shared SQLite database and links
venues to an owner via ``owner_id``.  Economy integration is minimal – a venue
costs ``rental_cost`` credits to create and half of that amount is refunded when
it is deleted.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from .economy_service import EconomyService, EconomyError

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class VenueService:
    def __init__(self, db_path: Optional[str] = None, economy: Optional[EconomyService] = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.economy = economy or EconomyService(self.db_path)
        self.economy.ensure_schema()
        self.ensure_schema()

    # ---------------- schema ----------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS venues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    city TEXT,
                    country TEXT,
                    capacity INTEGER,
                    rental_cost INTEGER NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT
                )
                """
            )
            conn.commit()

    # ---------------- helpers ----------------
    def _fetch(self, venue_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM venues WHERE id = ?", (venue_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    # ---------------- CRUD ----------------
    def create_venue(
        self,
        owner_id: int,
        name: str,
        city: str,
        country: str,
        capacity: int,
        rental_cost: int,
    ) -> Dict[str, Any]:
        if rental_cost < 0:
            raise ValueError("rental_cost must be non-negative")
        try:
            self.economy.withdraw(owner_id, rental_cost)
        except EconomyError as e:  # pragma: no cover - defensive
            raise ValueError(str(e)) from e
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO venues (owner_id, name, city, country, capacity, rental_cost)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (owner_id, name, city, country, capacity, rental_cost),
            )
            conn.commit()
            vid = int(cur.lastrowid or 0)
        return {
            "id": vid,
            "owner_id": owner_id,
            "name": name,
            "city": city,
            "country": country,
            "capacity": capacity,
            "rental_cost": rental_cost,
        }

    def list_venues(self, owner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            q = "SELECT * FROM venues"
            vals: List[Any] = []
            if owner_id is not None:
                q += " WHERE owner_id = ?"
                vals.append(owner_id)
            cur.execute(q, tuple(vals))
            return [dict(r) for r in cur.fetchall()]

    def update_venue(self, venue_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not updates:
            return self._fetch(venue_id) or {}
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            vals = list(updates.values()) + [venue_id]
            cur.execute(f"UPDATE venues SET {set_clause}, updated_at = datetime('now') WHERE id = ?", vals)
            if cur.rowcount == 0:
                return {}
            conn.commit()
        return self._fetch(venue_id) or {}

    def delete_venue(self, venue_id: int) -> bool:
        venue = self._fetch(venue_id)
        if not venue:
            return False
        refund = int(venue["rental_cost"] / 2)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM venues WHERE id = ?", (venue_id,))
            conn.commit()
        if refund:
            self.economy.deposit(venue["owner_id"], refund)
        return True

    def get_venue(self, venue_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch(venue_id)
