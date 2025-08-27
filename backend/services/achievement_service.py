from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from backend.models.achievement import Achievement, PlayerAchievement

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class AchievementService:
    """Service to manage achievements and player progress."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()
        self._ensure_default_definitions()

    # -------------------- schema --------------------
    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def ensure_schema(self) -> None:
        with self._conn() as conn:
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
            conn.commit()

    def _ensure_default_definitions(self) -> None:
        """Insert default achievement definitions if missing."""
        defaults = [
            ("chart_topper", "Chart Topper", "Reach #1 on any chart"),
            ("first_tour", "On the Road", "Confirm your first tour"),
            ("first_property", "Property Owner", "Purchase your first property"),
        ]
        with self._conn() as conn:
            cur = conn.cursor()
            for code, name, desc in defaults:
                cur.execute(
                    "INSERT OR IGNORE INTO achievements (code, name, description) VALUES (?, ?, ?)",
                    (code, name, desc),
                )
            conn.commit()

    # -------------------- operations --------------------
    def _achievement_id(self, code: str) -> int:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM achievements WHERE code = ?", (code,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Unknown achievement code: {code}")
            return int(row[0])

    def grant(self, user_id: int, code: str) -> bool:
        """Grant an achievement to a user. Returns True if newly unlocked."""
        aid = self._achievement_id(code)
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
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
            conn.commit()
            return True

    def revoke(self, user_id: int, code: str) -> bool:
        aid = self._achievement_id(code)
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM user_achievements WHERE user_id=? AND achievement_id=?",
                (user_id, aid),
            )
            conn.commit()
            return cur.rowcount > 0

    def list_achievements(self) -> List[Dict[str, str]]:
        with self._conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT code, name, description FROM achievements ORDER BY id")
            rows = cur.fetchall()
            return [dict(zip(["code", "name", "description"], r)) for r in rows]

    def get_user_achievements(self, user_id: int) -> List[Dict[str, Optional[str]]]:
        with self._conn() as conn:
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
                dict(zip(["code", "name", "description", "unlocked_at", "progress"], r)) for r in rows
            ]
