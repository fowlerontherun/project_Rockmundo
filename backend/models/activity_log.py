import json
import sqlite3
from typing import Dict, List

from backend.database import DB_PATH


def _ensure_table(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS activity_log (
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            slot INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            outcome_json TEXT NOT NULL,
            PRIMARY KEY (user_id, date, slot),
            FOREIGN KEY(user_id, date, slot) REFERENCES daily_schedule(user_id, date, slot),
            FOREIGN KEY(activity_id) REFERENCES activities(id)
        )
        """
    )
    cur.execute("PRAGMA table_info(activity_log)")
    columns = [row[1] for row in cur.fetchall()]
    if "slot" not in columns:
        cur.execute("ALTER TABLE activity_log RENAME TO activity_log_old")
        cur.execute(
            """
            CREATE TABLE activity_log (
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                slot INTEGER NOT NULL,
                activity_id INTEGER NOT NULL,
                outcome_json TEXT NOT NULL,
                PRIMARY KEY (user_id, date, slot),
                FOREIGN KEY(user_id, date, slot) REFERENCES daily_schedule(user_id, date, slot),
                FOREIGN KEY(activity_id) REFERENCES activities(id)
            )
            """
        )
        cur.execute(
            "INSERT INTO activity_log (user_id, date, slot, activity_id, outcome_json) SELECT user_id, date, 0, activity_id, outcome_json FROM activity_log_old"
        )
        cur.execute("DROP TABLE activity_log_old")


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
