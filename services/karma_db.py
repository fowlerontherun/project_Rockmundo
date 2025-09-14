from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Dict, Any

from database import DB_PATH
from backend.models.karma_event import KarmaEvent


class KarmaDB:
    """SQLite-backed persistence for karma events and user totals."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS karma_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    source TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_karma (
                    user_id INTEGER PRIMARY KEY,
                    total INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.commit()

    def insert_karma_event(self, event: KarmaEvent) -> int:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO karma_events (user_id, amount, reason, source, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event.user_id, event.amount, event.reason, event.source, event.timestamp),
            )
            conn.commit()
            return int(cur.lastrowid)

    def update_user_karma(self, user_id: int, amount: int) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO user_karma (user_id, total)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET total = total + excluded.total
                """,
                (user_id, amount),
            )
            conn.commit()

    def get_karma_events(self, user_id: int) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, user_id, amount, reason, source, timestamp
                FROM karma_events
                WHERE user_id = ?
                ORDER BY timestamp
                """,
                (user_id,),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "amount": row[2],
                    "reason": row[3],
                    "source": row[4],
                    "timestamp": row[5],
                }
                for row in rows
            ]

    def get_user_karma_total(self, user_id: int) -> int:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT total FROM user_karma WHERE user_id = ?",
                (user_id,),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0


__all__ = ["KarmaDB"]
