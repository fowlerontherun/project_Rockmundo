import json
import sqlite3
from typing import Dict, List

from backend.database import DB_PATH

def _ensure_row(cur: sqlite3.Cursor, user_id: int) -> None:
    cur.execute(
        """
        INSERT OR IGNORE INTO user_settings (user_id, theme, bio, links)
        VALUES (?, 'light', '', '[]')
        """,
        (user_id,)
    )


def get_settings(user_id: int) -> Dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    _ensure_row(cur, user_id)
    cur.execute(
        "SELECT theme, bio, links FROM user_settings WHERE user_id = ?",
        (user_id,)
    )
    theme, bio, links = cur.fetchone()
    conn.close()
    return {
        "theme": theme,
        "bio": bio or "",
        "links": json.loads(links or "[]"),
    }


def set_settings(user_id: int, theme: str, bio: str, links: List[str]) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO user_settings (user_id, theme, bio, links)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            theme = excluded.theme,
            bio = excluded.bio,
            links = excluded.links
        """,
        (user_id, theme, bio, json.dumps(links)),
    )
    conn.commit()
    conn.close()
