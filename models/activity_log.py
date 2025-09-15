import json
import sqlite3
from typing import Dict, List

from database import DB_PATH


def _ensure_table(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_log (
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            slot INTEGER NOT NULL DEFAULT 0,
            activity_id INTEGER NOT NULL,
            outcome_json TEXT NOT NULL,
            PRIMARY KEY (user_id, date, slot),
            FOREIGN KEY(user_id, date, slot) REFERENCES daily_schedule(user_id, date, slot),
            FOREIGN KEY(activity_id) REFERENCES activities(id)
        )
        """,
    )


def record_outcome(
    user_id: int, date: str, slot: int, activity_id: int, outcome: Dict
) -> None:
    """Persist an activity outcome linked to the schedule entry."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_table(cur)
        cur.execute(
            """
            INSERT OR REPLACE INTO activity_log
                (user_id, date, slot, activity_id, outcome_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, date, slot, activity_id, json.dumps(outcome)),
        )
        conn.commit()


def get_day_logs(user_id: int, date: str) -> List[Dict]:
    """Return all logged outcomes for a given day."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_table(cur)
        cur.execute(
            "SELECT slot, activity_id, outcome_json FROM activity_log WHERE user_id=? AND date=?",
            (user_id, date),
        )
        rows = cur.fetchall()
    return [
        {"slot": r[0], "activity_id": r[1], "outcome": json.loads(r[2])} for r in rows
    ]


__all__ = ["record_outcome", "get_day_logs"]
