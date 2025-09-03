import sqlite3
from typing import Iterable, List, Dict, Tuple

from backend.database import DB_PATH


def set_plan(user_id: int, day_of_week: str, entries: Iterable[Tuple[int, int]]) -> None:
    """Replace the default plan for a given day of week."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM default_schedule WHERE user_id = ? AND day_of_week = ?",
            (user_id, day_of_week),
        )
        for hour, activity_id in entries:
            cur.execute(
                "INSERT INTO default_schedule (user_id, day_of_week, hour, activity_id) VALUES (?, ?, ?, ?)",
                (user_id, day_of_week, hour, activity_id),
            )
        conn.commit()


def get_plan(user_id: int, day_of_week: str) -> List[Dict]:
    """Return the default plan for a user and day of week."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ds.hour, a.id, a.name, a.duration_hours, a.category
            FROM default_schedule ds
            JOIN activities a ON ds.activity_id = a.id
            WHERE ds.user_id = ? AND ds.day_of_week = ?
            ORDER BY ds.hour
            """,
            (user_id, day_of_week),
        )
        rows = cur.fetchall()
    return [
        {
            "hour": r[0],
            "activity": {
                "id": r[1],
                "name": r[2],
                "duration_hours": r[3],
                "category": r[4],
            },
        }
        for r in rows
    ]


__all__ = ["set_plan", "get_plan"]
