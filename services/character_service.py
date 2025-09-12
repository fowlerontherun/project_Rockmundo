"""Service layer for character CRUD operations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from schemas.character import CharacterCreate
from utils.db import get_conn


class CharacterService:
    """Simple CRUD operations for characters backed by SQLite."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path
        self._ensure_table()

    # ------------------------------------------------------------------
    def _ensure_table(self) -> None:
        """Ensure the ``characters`` table exists."""
        with get_conn(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    genre TEXT NOT NULL,
                    trait TEXT NOT NULL,
                    birthplace TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )

    # ------------------------------------------------------------------
    def list_characters(self) -> List[Dict[str, Any]]:
        with get_conn(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, name, genre, trait, birthplace, created_at FROM characters"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_character(self, character_id: int) -> Optional[Dict[str, Any]]:
        with get_conn(self.db_path) as conn:
            row = conn.execute(
                "SELECT id, name, genre, trait, birthplace, created_at FROM characters WHERE id=?",
                (character_id,),
            ).fetchone()
            return dict(row) if row else None

    def create_character(self, character: CharacterCreate) -> Dict[str, Any]:
        with get_conn(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO characters (name, genre, trait, birthplace)
                VALUES (?, ?, ?, ?)
                """,
                (character.name, character.genre, character.trait, character.birthplace),
            )
            char_id = int(cur.lastrowid)
            row = conn.execute(
                "SELECT id, name, genre, trait, birthplace, created_at FROM characters WHERE id=?",
                (char_id,),
            ).fetchone()
            return dict(row)

    def update_character(self, character_id: int, character: CharacterCreate) -> Optional[Dict[str, Any]]:
        with get_conn(self.db_path) as conn:
            cur = conn.execute(
                """
                UPDATE characters
                SET name=?, genre=?, trait=?, birthplace=?
                WHERE id=?
                """,
                (character.name, character.genre, character.trait, character.birthplace, character_id),
            )
            if cur.rowcount == 0:
                return None
            row = conn.execute(
                "SELECT id, name, genre, trait, birthplace, created_at FROM characters WHERE id=?",
                (character_id,),
            ).fetchone()
            return dict(row)

    def delete_character(self, character_id: int) -> bool:
        with get_conn(self.db_path) as conn:
            cur = conn.execute("DELETE FROM characters WHERE id=?", (character_id,))
            return cur.rowcount > 0


character_service = CharacterService()

__all__ = ["CharacterService", "character_service"]
