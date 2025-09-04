import sqlite3
from typing import List, Dict

from backend.database import DB_PATH


def add_entry(band_id: int, date: str, slot: int, activity_id: int) -> None:
    """Insert or update a band schedule entry."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO band_schedule (band_id, date, slot, activity_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(band_id, date, slot)
            DO UPDATE SET activity_id = excluded.activity_id
            """,
            (band_id, date, slot, activity_id),
        )
        conn.commit()


def get_schedule(band_id: int, date: str) -> List[Dict]:
    """Return all scheduled band activities for a given date."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT bs.slot, a.id, a.name, a.duration_hours, a.category
            FROM band_schedule bs
            JOIN activities a ON bs.activity_id = a.id
            WHERE bs.band_id = ? AND bs.date = ?
            ORDER BY bs.slot
            """,
            (band_id, date),
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
