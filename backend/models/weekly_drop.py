import sqlite3
from datetime import date
from typing import Dict, Optional

from backend.database import DB_PATH


def schedule_drop(user_id: int, drop_date: str, reward: str) -> None:
    """Record a pending weekly reward drop for a user."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT OR REPLACE INTO weekly_drops (user_id, drop_date, reward, claimed)
        VALUES (?, ?, ?, 0)
        """,
        (user_id, drop_date, reward),
    )
    conn.commit()
    conn.close()


def get_next_drop(user_id: int) -> Optional[Dict[str, str]]:
    """Return the next unclaimed drop for the user, if any."""
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT drop_date, reward FROM weekly_drops
        WHERE user_id = ? AND claimed = 0 AND drop_date >= ?
        ORDER BY drop_date LIMIT 1
        """,
        (user_id, today),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"drop_date": row[0], "reward": row[1]}
    return None


def claim_drop(user_id: int, drop_date: str) -> bool:
    """Mark a drop as claimed; return True if updated."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE weekly_drops SET claimed = 1 WHERE user_id = ? AND drop_date = ?",
        (user_id, drop_date),
    )
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed
