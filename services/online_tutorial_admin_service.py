"""Admin service for managing online tutorials in SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

from models.online_tutorial import OnlineTutorial

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class OnlineTutorialAdminService:
    """CRUD helpers for online tutorials."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS online_tutorials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_url TEXT NOT NULL,
                    skill TEXT NOT NULL,
                    xp_rate INTEGER NOT NULL,
                    plateau_level INTEGER NOT NULL,
                    rarity_weight INTEGER NOT NULL
                )
                """,
            )
            conn.commit()

    def list_tutorials(self) -> List[OnlineTutorial]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, video_url, skill, xp_rate, plateau_level, rarity_weight FROM online_tutorials ORDER BY id"
            )
            rows = cur.fetchall()
            return [OnlineTutorial(**dict(row)) for row in rows]

    def create_tutorial(self, tutorial: OnlineTutorial) -> OnlineTutorial:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO online_tutorials (video_url, skill, xp_rate, plateau_level, rarity_weight) VALUES (?, ?, ?, ?, ?)",
                (
                    tutorial.video_url,
                    tutorial.skill,
                    tutorial.xp_rate,
                    tutorial.plateau_level,
                    tutorial.rarity_weight,
                ),
            )
            tutorial.id = cur.lastrowid
            conn.commit()
            return tutorial

    def update_tutorial(self, tutorial_id: int, **changes) -> OnlineTutorial:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, video_url, skill, xp_rate, plateau_level, rarity_weight FROM online_tutorials WHERE id = ?",
                (tutorial_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Tutorial not found")
            data = dict(row)
            for k, v in changes.items():
                if k in data and v is not None:
                    data[k] = v
            cur.execute(
                "UPDATE online_tutorials SET video_url=?, skill=?, xp_rate=?, plateau_level=?, rarity_weight=? WHERE id=?",
                (
                    data["video_url"],
                    data["skill"],
                    data["xp_rate"],
                    data["plateau_level"],
                    data["rarity_weight"],
                    tutorial_id,
                ),
            )
            conn.commit()
            return OnlineTutorial(**data)

    def delete_tutorial(self, tutorial_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM online_tutorials WHERE id=?", (tutorial_id,))
            conn.commit()

    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM online_tutorials")
            conn.commit()


online_tutorial_admin_service = OnlineTutorialAdminService()


def get_online_tutorial_admin_service() -> OnlineTutorialAdminService:
    return online_tutorial_admin_service


__all__ = [
    "OnlineTutorialAdminService",
    "online_tutorial_admin_service",
    "get_online_tutorial_admin_service",
]
