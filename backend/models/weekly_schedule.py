import sqlite3
from typing import List, Dict, Iterable, Tuple

from backend.database import DB_PATH


def add_entry(user_id: int, week_start: str, day: str, slot: int, activity_id: int) -> None:
    """Insert or update a weekly schedule entry."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO weekly_schedule (user_id, week_start, day, slot, activity_id)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, week_start, day, slot)
            DO UPDATE SET activity_id = excluded.activity_id
            """,
            (user_id, week_start, day, slot, activity_id),
        )
        conn.commit()


def update_entry(user_id: int, week_start: str, day: str, slot: int, activity_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE weekly_schedule SET activity_id = ? WHERE user_id = ? AND week_start = ? AND day = ? AND slot = ?",
            (activity_id, user_id, week_start, day, slot),
        )
        conn.commit()


def remove_entry(user_id: int, week_start: str, day: str, slot: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM weekly_schedule WHERE user_id = ? AND week_start = ? AND day = ? AND slot = ?",
            (user_id, week_start, day, slot),
        )
        conn.commit()


def set_schedule(user_id: int, week_start: str, entries: Iterable[Tuple[str, int, int]]) -> None:
    """Replace the entire schedule for a given week."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM weekly_schedule WHERE user_id = ? AND week_start = ?",
            (user_id, week_start),
        )
        for day, slot, activity_id in entries:
            cur.execute(
                "INSERT INTO weekly_schedule (user_id, week_start, day, slot, activity_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, week_start, day, slot, activity_id),
            )
        conn.commit()


def get_schedule(user_id: int, week_start: str) -> List[Dict]:
    """Return all scheduled activities for a given week."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ws.day, ws.slot, a.id, a.name, a.duration_hours, a.category
            FROM weekly_schedule ws
            JOIN activities a ON ws.activity_id = a.id
            WHERE ws.user_id = ? AND ws.week_start = ?
            ORDER BY ws.day, ws.slot
            """,
            (user_id, week_start),
        )
        rows = cur.fetchall()
    return [
        {
            "day": r[0],
            "slot": r[1],
            "activity": {
                "id": r[2],
                "name": r[3],
                "duration_hours": r[4],
                "category": r[5],
            },
        }
        for r in rows
    ]


__all__ = [
    "add_entry",
    "update_entry",
    "remove_entry",
    "set_schedule",
    "get_schedule",
]
