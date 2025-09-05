"""Hidden XP reward utilities."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class XPRewardService:
    """Utility service for awarding hidden XP to new or low-level players."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(db_path or DB_PATH)

    # ------------------------------------------------------------------
    def _ensure_schema(self, cur: sqlite3.Cursor) -> None:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS hidden_xp_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )

    def _is_new_or_low_level(self, cur: sqlite3.Cursor, user_id: int) -> bool:
        """Return True if the account is new or low level.

        The checks are best-effort and tolerate missing tables.
        """
        # Recently created account?
        try:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'"
            )
            if cur.fetchone():
                cur.execute(
                    "SELECT created_at FROM accounts WHERE user_id = ?", (user_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return True
                try:
                    created = datetime.fromisoformat(row[0])
                    if datetime.utcnow() - created <= timedelta(days=7):
                        return True
                except Exception:
                    pass
        except Exception:
            pass

        # Low level?
        try:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='user_levels'"
            )
            if cur.fetchone():
                cur.execute(
                    "SELECT level FROM user_levels WHERE user_id = ?", (user_id,),
                )
                row = cur.fetchone()
                if row and int(row[0]) <= 5:
                    return True
        except Exception:
            pass
        return False

    # ------------------------------------------------------------------
    def grant_hidden_xp(
        self,
        user_id: int,
        reason: str,
        amount: int = 10,
        conn: sqlite3.Connection | None = None,
    ) -> bool:
        """Grant hidden XP to the given user if they qualify.

        Parameters
        ----------
        user_id:
            Recipient of the secret XP.
        reason:
            Context for auditing, e.g. ``gift`` or ``transfer``.
        amount:
            Amount of XP to award. Defaults to 10.
        conn:
            Optional existing SQLite connection to use. When provided, the
            caller is responsible for committing.
        Returns
        -------
        bool
            ``True`` if XP was granted, ``False`` otherwise.
        """
        if conn is None:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                self._ensure_schema(cur)
                if not self._is_new_or_low_level(cur, user_id):
                    return False
                cur.execute(
                    "INSERT INTO hidden_xp_rewards (user_id, amount, reason) VALUES (?, ?, ?)",
                    (user_id, amount, reason),
                )
                try:
                    cur.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='user_xp'",
                    )
                    if cur.fetchone():
                        cur.execute(
                            """
                            INSERT INTO user_xp(user_id, xp)
                            VALUES (?, ?)
                            ON CONFLICT(user_id) DO UPDATE SET xp = xp + excluded.xp
                            """,
                            (user_id, amount),
                        )
                except Exception:
                    pass
                conn.commit()
                return True

        cur = conn.cursor()
        self._ensure_schema(cur)
        if not self._is_new_or_low_level(cur, user_id):
            return False
        cur.execute(
            "INSERT INTO hidden_xp_rewards (user_id, amount, reason) VALUES (?, ?, ?)",
            (user_id, amount, reason),
        )
        try:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='user_xp'",
            )
            if cur.fetchone():
                cur.execute(
                    """
                    INSERT INTO user_xp(user_id, xp)
                    VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET xp = xp + excluded.xp
                    """,
                    (user_id, amount),
                )
        except Exception:
            pass
        return True

    # ------------------------------------------------------------------
    def grant_daily_reward(self, user_id: int, tier: int) -> bool:
        """Award XP for completing the daily challenge.

        The amount scales with the provided ``tier``.
        """
        amount = 10 * max(1, int(tier))
        return self.grant_hidden_xp(user_id, f"daily_tier_{tier}", amount)


xp_reward_service = XPRewardService()

__all__ = ["XPRewardService", "xp_reward_service"]

