import json
import sqlite3
from typing import Dict, List

from backend.database import DB_PATH


def _ensure_row(cur: sqlite3.Cursor, user_id: int) -> None:
    cur.execute(
        """
        INSERT OR IGNORE INTO user_settings (user_id, theme, bio, links, timezone, auto_reschedule)
        VALUES (?, 'light', '', '[]', 'UTC', 1)
        """,
        (user_id,),
    )


def get_settings(user_id: int) -> Dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    _ensure_row(cur, user_id)
    cur.execute(
        "SELECT theme, bio, links, timezone, auto_reschedule FROM user_settings WHERE user_id = ?",
        (user_id,),
    )
    theme, bio, links, tz, auto = cur.fetchone()
    conn.close()
    return {
        "theme": theme,
        "bio": bio or "",
        "links": json.loads(links or "[]"),
        "timezone": tz or "UTC",
        "auto_reschedule": bool(auto),
    }


def set_settings(
    user_id: int,
    theme: str,
    bio: str,
    links: List[str],
    timezone: str,
    auto_reschedule: bool = True,
) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO user_settings (user_id, theme, bio, links, timezone, auto_reschedule)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            theme = excluded.theme,
            bio = excluded.bio,
            links = excluded.links,
            timezone = excluded.timezone,
            auto_reschedule = excluded.auto_reschedule
        """,
        (user_id, theme, bio, json.dumps(links), timezone, int(auto_reschedule)),
    )
    conn.commit()
    conn.close()
