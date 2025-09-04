import sqlite3
from typing import Dict, List

from backend import database


def _ensure_table(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recurring_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pattern TEXT NOT NULL,
            hour INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(activity_id) REFERENCES activities(id)
        )
        """,
    )


def add_template(user_id: int, pattern: str, hour: int, activity_id: int, active: bool = True) -> int:
    """Create a recurring schedule template."""
    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_table(cur)
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
    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_table(cur)
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
    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_table(cur)
        cur.execute("DELETE FROM recurring_schedule WHERE id = ?", (template_id,))
        conn.commit()


def get_templates(user_id: int) -> List[Dict]:
    with sqlite3.connect(database.DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_table(cur)
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
