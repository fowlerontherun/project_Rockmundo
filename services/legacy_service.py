from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from database import DB_PATH


class LegacyService:
    """Service for tracking band milestones and career scores."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)

    # -------- schema --------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS legacy_milestones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    band_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    points INTEGER NOT NULL,
                    achieved_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_legacy_band ON legacy_milestones(band_id)"
            )
            conn.commit()

    # -------- actions --------
    def log_milestone(
        self, band_id: int, category: str, description: str, points: int
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO legacy_milestones (band_id, category, description, points)
                VALUES (?, ?, ?, ?)
                """,
                (band_id, category, description, points),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    # -------- queries --------
    def get_history(self, band_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, band_id, category, description, points, achieved_at
                FROM legacy_milestones
                WHERE band_id = ?
                ORDER BY achieved_at ASC
                """,
                (band_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def compute_score(self, band_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COALESCE(SUM(points), 0) FROM legacy_milestones WHERE band_id = ?",
                (band_id,),
            )
            row = cur.fetchone()
            return int(row[0] or 0)

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, int]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT band_id, SUM(points) AS score
                FROM legacy_milestones
                GROUP BY band_id
                ORDER BY score DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]
