import sqlite3
import sqlite3
import sqlite3
from typing import List, Dict

from backend.database import DB_PATH


def add_entry(user_id: int, date: str, slot: int, activity_id: int) -> None:
    """Insert or update a schedule entry for a user."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO daily_schedule (user_id, date, slot, hour, activity_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date, slot) DO UPDATE SET activity_id = excluded.activity_id, hour = excluded.hour
            """,
            (user_id, date, slot, slot, activity_id),
        )
        conn.commit()


def update_entry(user_id: int, date: str, slot: int, activity_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE daily_schedule SET activity_id = ?, hour = ? WHERE user_id = ? AND date = ? AND slot = ?",
            (activity_id, slot, user_id, date, slot),
        )
        conn.commit()


def remove_entry(user_id: int, date: str, slot: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM daily_schedule WHERE user_id = ? AND date = ? AND slot = ?",
            (user_id, date, slot),
        )
        conn.commit()


def get_schedule(user_id: int, date: str) -> List[Dict]:
    """Return all scheduled activities for a user on a given date."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ds.slot, a.id, a.name, a.duration_hours, a.category
            FROM daily_schedule ds
            JOIN activities a ON ds.activity_id = a.id
            WHERE ds.user_id = ? AND ds.date = ?
            ORDER BY ds.slot
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


__all__ = ["add_entry", "update_entry", "remove_entry", "get_schedule"]
