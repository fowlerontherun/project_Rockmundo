import sqlite3
from datetime import datetime
from typing import List, Dict

from backend.database import DB_PATH

DECAY_FACTOR = 0.95


def _ensure_schema(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS song_popularity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            popularity_score REAL NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )


def add_event(song_id: int, amount: float, source: str) -> float:
    """Boost a song's popularity by a given amount from some source."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_schema(cur)
        cur.execute(
            "SELECT popularity_score FROM song_popularity WHERE song_id=? ORDER BY updated_at DESC LIMIT 1",
            (song_id,),
        )
        row = cur.fetchone()
        current = float(row[0]) if row else 0.0
        new_score = current + float(amount)
        cur.execute(
            "INSERT INTO song_popularity (song_id, popularity_score, updated_at) VALUES (?, ?, ?)",
            (song_id, new_score, datetime.utcnow().isoformat()),
        )
        conn.commit()
        return new_score


def apply_decay() -> int:
    """Apply exponential decay to all songs' popularity scores."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_schema(cur)
        cur.execute(
            """
            SELECT song_id, popularity_score FROM song_popularity
            WHERE (song_id, updated_at) IN (
                SELECT song_id, MAX(updated_at) FROM song_popularity GROUP BY song_id
            )
            """
        )
        rows = cur.fetchall()
        now = datetime.utcnow().isoformat()
        decayed = [
            (song_id, score * DECAY_FACTOR, now)
            for song_id, score in rows
        ]
        if decayed:
            cur.executemany(
                "INSERT INTO song_popularity (song_id, popularity_score, updated_at) VALUES (?, ?, ?)",
                decayed,
            )
        conn.commit()
        return len(decayed)


def get_history(song_id: int) -> List[Dict[str, float]]:
    """Return the popularity history for a song."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        _ensure_schema(cur)
        cur.execute(
            "SELECT popularity_score, updated_at FROM song_popularity WHERE song_id=? ORDER BY updated_at",
            (song_id,),
        )
        return [dict(r) for r in cur.fetchall()]
