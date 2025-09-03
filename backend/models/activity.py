import sqlite3
from typing import List, Optional, Dict

from backend.database import DB_PATH


def create_activity(name: str, duration_hours: int, category: str) -> int:
    """Insert a new activity and return its id."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO activities (name, duration_hours, category) VALUES (?, ?, ?)",
            (name, duration_hours, category),
        )
        conn.commit()
        return cur.lastrowid


def get_activity(activity_id: int) -> Optional[Dict]:
    """Retrieve an activity by id."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, duration_hours, category FROM activities WHERE id = ?",
            (activity_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "duration_hours": row[2],
        "category": row[3],
    }


def list_activities() -> List[Dict]:
    """Return all activities."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, duration_hours, category FROM activities")
        rows = cur.fetchall()
    return [
        {"id": r[0], "name": r[1], "duration_hours": r[2], "category": r[3]}
        for r in rows
    ]


def update_activity(activity_id: int, name: str, duration_hours: int, category: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE activities SET name = ?, duration_hours = ?, category = ? WHERE id = ?",
            (name, duration_hours, category, activity_id),
        )
        conn.commit()


def delete_activity(activity_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        conn.commit()


__all__ = [
    "create_activity",
    "get_activity",
    "list_activities",
    "update_activity",
    "delete_activity",
]
