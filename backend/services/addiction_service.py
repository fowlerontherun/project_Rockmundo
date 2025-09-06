from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from backend.database import DB_PATH


class AddictionService:
    """Basic persistence and logic for user addictions."""

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS addiction (
                    user_id INTEGER NOT NULL,
                    substance TEXT NOT NULL,
                    level INTEGER NOT NULL DEFAULT 0,
                    last_used TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, substance)
                )
                """
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def use(self, user_id: int, substance: str, amount: int = 10) -> int:
        """Record substance use and increase addiction level."""

        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT level FROM addiction WHERE user_id = ? AND substance = ?",
                (user_id, substance),
            )
            row = cur.fetchone()
            if row:
                level = min(100, row[0] + amount)
                cur.execute(
                    """UPDATE addiction
                    SET level = ?, last_used = ?, updated_at = ?
                    WHERE user_id = ? AND substance = ?""",
                    (level, now, now, user_id, substance),
                )
            else:
                level = min(100, amount)
                cur.execute(
                    """INSERT INTO addiction
                    (user_id, substance, level, last_used, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (user_id, substance, level, now, now, now),
                )
            conn.commit()
        return level

    def update_addiction(self, user_id: int, substance: str) -> dict[str, object]:
        """Increase addiction level and return immediate buffs."""

        level = self.use(user_id, substance)
        return {"addiction_level": level, "buffs": [substance]}

    def apply_withdrawal(self, user_id: int, decay: int = 5) -> None:
        """Apply daily withdrawal decay to all addictions."""

        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT substance, level FROM addiction WHERE user_id = ?",
                (user_id,),
            )
            rows = cur.fetchall()
            for substance, level in rows:
                new_level = max(0, level - decay)
                cur.execute(
                    """UPDATE addiction
                    SET level = ?, updated_at = ?
                    WHERE user_id = ? AND substance = ?""",
                    (new_level, now, user_id, substance),
                )
            conn.commit()

    def get_level(self, user_id: int, substance: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT level FROM addiction WHERE user_id = ? AND substance = ?",
                (user_id, substance),
            )
            row = cur.fetchone()
            return row[0] if row else 0

    def get_highest_level(self, user_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT MAX(level) FROM addiction WHERE user_id = ?",
                (user_id,),
            )
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else 0

    def check_for_missed_events(self, user_id: int, day: str) -> list[dict]:
        """Return scheduled events to cancel if addiction level is high.

        When a user's highest addiction level for any substance reaches 70 or
        more, they are considered unreliable for the day.  This helper returns
        any scheduled events for ``day`` that should be cancelled by the
        scheduler.  The method does not mutate the schedule; callers are
        expected to remove the returned entries themselves.
        """

        level = self.get_highest_level(user_id)
        if level < 70:
            return []

        from backend.models.daily_schedule import get_schedule  # local import

        return get_schedule(user_id, day)


# Singleton instance
addiction_service = AddictionService()
