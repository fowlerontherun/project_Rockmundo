import sqlite3
from typing import Optional

from database import DB_PATH


def set_reward(tier: int, reward: str) -> None:
    """Define or update the reward for a tier."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO tier_tracks (tier, reward) VALUES (?, ?)",
        (tier, reward),
    )
    conn.commit()
    conn.close()


def get_reward(tier: int) -> Optional[str]:
    """Return the reward for the given tier, if configured."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT reward FROM tier_tracks WHERE tier = ?", (tier,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
