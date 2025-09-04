import sqlite3
from typing import List, Dict

from backend.database import DB_PATH


def add_template(user_id: int, pattern: str, hour: int, activity_id: int, active: bool = True) -> int:
    """Create a recurring schedule template."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO recurring_schedule (user_id, pattern, hour, activity_id, active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, pattern, hour, activity_id, int(active)),
        )
        conn.commit()
        return cur.lastrowid


def update_template(template_id: int, pattern: str, hour: int, activity_id: int, active: bool = True) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE recurring_schedule
            SET pattern = ?, hour = ?, activity_id = ?, active = ?
            WHERE id = ?
            """,
            (pattern, hour, activity_id, int(active), template_id),
        )
        conn.commit()


def remove_template(template_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM recurring_schedule WHERE id = ?", (template_id,))
        conn.commit()


def get_templates(user_id: int) -> List[Dict]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT rs.id, rs.pattern, rs.hour, rs.active,
                   a.id, a.name, a.duration_hours, a.category
            FROM recurring_schedule rs
            JOIN activities a ON rs.activity_id = a.id
            WHERE rs.user_id = ?
            ORDER BY rs.id
            """,
            (user_id,),
        )
        rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "pattern": r[1],
            "hour": r[2],
            "active": bool(r[3]),
            "activity": {
                "id": r[4],
                "name": r[5],
                "duration_hours": r[6],
                "category": r[7],
            },
        }
        for r in rows
    ]


__all__ = ["add_template", "update_template", "remove_template", "get_templates"]
