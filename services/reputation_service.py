from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from database import DB_PATH
from backend.models.reputation import ReputationEvent

class ReputationService:
    """Persist and mutate reputation scores and events."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self._ensure_schema()

    # ------------------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS reputation_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    change INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    source TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_reputation (
                    user_id INTEGER PRIMARY KEY,
                    total INTEGER NOT NULL DEFAULT 0
                )
                """,
            )
            conn.commit()

    # ------------------------------------------------------------------
    def _record(self, user_id: int, amount: int, reason: str, source: str) -> None:
        event = ReputationEvent(
            user_id=user_id,
            change=amount,
            reason=reason,
            source=source,
            timestamp=datetime.utcnow().isoformat(),
        )
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO reputation_events (user_id, change, reason, source, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event.user_id, event.change, event.reason, event.source, event.timestamp),
            )
            cur.execute(
                """
                INSERT INTO user_reputation (user_id, total)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET total = total + excluded.total
                """,
                (user_id, amount),
            )
            conn.commit()

    # ------------------------------------------------------------------
    def record_gig(self, user_id: int, points: int = 10) -> None:
        """Award reputation for completing a gig."""

        self._record(user_id, points, "gig", "gig")

    def record_release(self, user_id: int, points: int = 20) -> None:
        """Award reputation for releasing music."""

        self._record(user_id, points, "release", "release")

    def record_achievement(self, user_id: int, points: int = 30) -> None:
        """Award reputation for unlocking an achievement."""

        self._record(user_id, points, "achievement", "achievement")

    # ------------------------------------------------------------------
    def get_reputation(self, user_id: int) -> int:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT total FROM user_reputation WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return int(row[0]) if row else 0

    def get_history(self, user_id: int) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, user_id, change, reason, source, timestamp
                  FROM reputation_events
                 WHERE user_id = ?
                 ORDER BY id
                """,
                (user_id,),
            )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "user_id": r[1],
                    "change": r[2],
                    "reason": r[3],
                    "source": r[4],
                    "timestamp": r[5],
                }
                for r in rows
            ]


reputation_service = ReputationService()

__all__ = ["ReputationService", "reputation_service"]
