"""Achievement service for managing definitions and user progress."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from backend.models.achievement import Achievement, PlayerAchievement
from core.config import settings
from utils.db import get_conn


class AchievementService:
    """Service to manage achievements and player progress."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize the service.

        Args:
            db_path: Optional path to the SQLite database. Defaults to
                :data:`core.config.settings.DB_PATH`.
        """

        self.db_path = db_path or settings.DB_PATH
        self.ensure_schema()
        self._ensure_default_definitions()

    # -------------------- schema --------------------
    def ensure_schema(self) -> None:
        """Create required database tables if they do not already exist."""

        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_achievements (
                    user_id INTEGER NOT NULL,
                    achievement_id INTEGER NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    unlocked_at TEXT,
                    PRIMARY KEY (user_id, achievement_id),
                    FOREIGN KEY (achievement_id) REFERENCES achievements(id)
                )
                """
            )

    def _ensure_default_definitions(self) -> None:
        """Insert default achievement definitions if missing."""

        defaults = [
            ("chart_topper", "Chart Topper", "Reach #1 on any chart"),
            ("first_tour", "On the Road", "Confirm your first tour"),
            ("first_property", "Property Owner", "Purchase your first property"),
        ]
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            for code, name, desc in defaults:
                cur.execute(
                    "INSERT OR IGNORE INTO achievements (code, name, description) VALUES (?, ?, ?)",
                    (code, name, desc),
                )

    # -------------------- operations --------------------
    def _achievement_id(self, code: str) -> int:
        """Resolve an achievement code to its database ID.

        Args:
            code: Unique achievement code.

        Returns:
            The integer primary key for the achievement.

        Raises:
            ValueError: If the achievement code is unknown.
        """

        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM achievements WHERE code = ?", (code,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Unknown achievement code: {code}")
            return int(row[0])

    def grant(self, user_id: int, code: str) -> bool:
        """Grant an achievement to a user.

        Args:
            user_id: Identifier of the user receiving the achievement.
            code: Achievement code to grant.

        Returns:
            ``True`` if the achievement was newly unlocked, ``False`` otherwise.
        """

        aid = self._achievement_id(code)
        now = datetime.utcnow().isoformat()
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT unlocked_at FROM user_achievements WHERE user_id=? AND achievement_id=?",
                (user_id, aid),
            )
            row = cur.fetchone()
            if row and row[0]:
                return False
            if row:
                cur.execute(
                    "UPDATE user_achievements SET unlocked_at=?, progress=progress WHERE user_id=? AND achievement_id=?",
                    (now, user_id, aid),
                )
            else:
                cur.execute(
                    "INSERT INTO user_achievements (user_id, achievement_id, progress, unlocked_at) VALUES (?, ?, 0, ?)",
                    (user_id, aid, now),
                )
            return True

    def revoke(self, user_id: int, code: str) -> bool:
        """Revoke an achievement from a user.

        Args:
            user_id: Identifier of the user.
            code: Achievement code to revoke.

        Returns:
            ``True`` if a record was removed, ``False`` otherwise.
        """

        aid = self._achievement_id(code)
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM user_achievements WHERE user_id=? AND achievement_id=?",
                (user_id, aid),
            )
            return cur.rowcount > 0

    def list_achievements(self) -> List[Dict[str, str]]:
        """Return all defined achievements.

        Returns:
            A list of dictionaries with keys ``code``, ``name`` and ``description``.
        """

        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT code, name, description FROM achievements ORDER BY id")
            rows = cur.fetchall()
            return [dict(zip(["code", "name", "description"], r)) for r in rows]

    def get_user_achievements(self, user_id: int) -> List[Dict[str, Optional[str]]]:
        """Retrieve achievement progress for a user.

        Args:
            user_id: Identifier of the user.

        Returns:
            A list of dictionaries containing achievement data and progress
            information.
        """

        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT a.code, a.name, a.description, ua.unlocked_at, ua.progress
                FROM achievements a
                LEFT JOIN user_achievements ua ON ua.achievement_id = a.id AND ua.user_id = ?
                ORDER BY a.id
                """,
                (user_id,),
            )
            rows = cur.fetchall()
            return [
                dict(zip(["code", "name", "description", "unlocked_at", "progress"], r))
                for r in rows
            ]

