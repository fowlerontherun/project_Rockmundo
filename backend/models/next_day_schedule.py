import sqlite3
from typing import Dict, List

from backend.database import DB_PATH


def add_entry(user_id: int, date: str, slot: int, activity_id: int) -> None:
    """Insert or replace a rescheduled activity for the given date."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO next_day_schedule (user_id, date, slot, activity_id)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, date, slot, activity_id),
        )
        conn.commit()


def get_schedule(user_id: int, date: str) -> List[Dict]:
    """Return all rescheduled activities for a user on a given date."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT nds.slot, a.id, a.name, a.duration_hours, a.category
            FROM next_day_schedule nds
            JOIN activities a ON nds.activity_id = a.id
            WHERE nds.user_id = ? AND nds.date = ?
            ORDER BY nds.slot
            """,
            (user_id, date),
        )
        rows = cur.fetchall()
    return [
        {
            "slot": r[0],
            "activity": {
                "id": r[1],
                "name": r[2],
                "duration_hours": r[3],
                "category": r[4],
            },
        }
        for r in rows
    ]


__all__ = ["add_entry", "get_schedule"]
