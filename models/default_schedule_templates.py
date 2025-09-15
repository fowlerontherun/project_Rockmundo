import sqlite3
import sqlite3
from typing import Iterable, List, Dict, Tuple

from database import DB_PATH


def create_template(user_id: int, name: str, entries: Iterable[Tuple[int, int]]) -> int:
    """Create a new schedule template with the provided entries."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO default_schedule_templates (user_id, name) VALUES (?, ?)",
            (user_id, name),
        )
        template_id = cur.lastrowid
        for hour, activity_id in entries:
            cur.execute(
                "INSERT INTO default_schedule_entries (template_id, hour, activity_id) VALUES (?, ?, ?)",
                (template_id, hour, activity_id),
            )
        conn.commit()
    return template_id


def set_entries(template_id: int, entries: Iterable[Tuple[int, int]]) -> None:
    """Replace all entries for a template."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM default_schedule_entries WHERE template_id = ?",
            (template_id,),
        )
        for hour, activity_id in entries:
            cur.execute(
                "INSERT INTO default_schedule_entries (template_id, hour, activity_id) VALUES (?, ?, ?)",
                (template_id, hour, activity_id),
            )
        conn.commit()


def delete_template(template_id: int) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM default_schedule_entries WHERE template_id = ?",
            (template_id,),
        )
        cur.execute(
            "DELETE FROM default_schedule_templates WHERE id = ?",
            (template_id,),
        )
        conn.commit()


def list_templates(user_id: int) -> List[Dict]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name FROM default_schedule_templates WHERE user_id = ? ORDER BY id",
            (user_id,),
        )
        rows = cur.fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]


def get_entries(template_id: int) -> List[Tuple[int, int]]:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT hour, activity_id FROM default_schedule_entries WHERE template_id = ? ORDER BY hour",
            (template_id,),
        )
        rows = cur.fetchall()
    return [(r[0], r[1]) for r in rows]


__all__ = [
    "create_template",
    "set_entries",
    "delete_template",
    "list_templates",
    "get_entries",
]
