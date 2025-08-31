import json
import sqlite3
from datetime import datetime

from backend.database import DB_PATH


def store_setlist_summary(summary: dict) -> None:
    """Persist a setlist summary for later review."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS setlist_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            performance_id INTEGER,
            summary TEXT,
            created_at TEXT
        )
        """
    )
    cur.execute(
        "INSERT INTO setlist_summaries (performance_id, summary, created_at) VALUES (?, ?, ?)",
        (summary.get("performance_id"), json.dumps(summary), datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_setlist_summary(performance_id: int):
    """Retrieve a stored setlist summary."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT summary FROM setlist_summaries WHERE performance_id = ?",
        (performance_id,),
    )
    row = cur.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None

