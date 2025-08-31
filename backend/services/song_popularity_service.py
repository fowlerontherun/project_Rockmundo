import math
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from backend.database import DB_PATH


# Popularity decays by this factor every day
DECAY_FACTOR = 0.95
# Derived half-life in days for the current decay factor
HALF_LIFE_DAYS = math.log(0.5) / math.log(DECAY_FACTOR)


def _ensure_schema(cur: sqlite3.Cursor) -> None:
    """Ensure required tables exist."""
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
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS song_popularity_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            boost INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )


class SongPopularityService:
    """Track song popularity boosts from various media events."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or DB_PATH

    def add_event(self, song_id: int, source: str, boost: int) -> Dict[str, int]:
        """Apply a popularity boost and log the event."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            _ensure_schema(cur)
            now = datetime.utcnow().isoformat()
            cur.execute(
                "INSERT INTO song_popularity_events (song_id, source, boost, created_at) VALUES (?, ?, ?, ?)",
                (song_id, source, boost, now),
            )
            cur.execute(
                "INSERT INTO song_popularity (song_id, score) VALUES (?, ?) "
                "ON CONFLICT(song_id) DO UPDATE SET score = score + excluded.score",
                (song_id, boost),
            )
            cur.execute(
                "SELECT score FROM song_popularity WHERE song_id = ?",
                (song_id,),
            )
            row = cur.fetchone()
            return {"song_id": song_id, "score": int(row[0] if row else 0)}

    def list_events(self, song_id: Optional[int] = None) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            _ensure_schema(cur)
            if song_id is None:
                cur.execute(
                    "SELECT id, song_id, source, boost, created_at FROM song_popularity_events ORDER BY id DESC"
                )
            else:
                cur.execute(
                    "SELECT id, song_id, source, boost, created_at FROM song_popularity_events "
                    "WHERE song_id = ? ORDER BY id DESC",
                    (song_id,),
                )
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "song_id": r[1],
                    "source": r[2],
                    "boost": r[3],
                    "created_at": r[4],
                }
                for r in rows
            ]


# Singleton used across the app
song_popularity_service = SongPopularityService()


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
        now = datetime.utcnow().isoformat()
        cur.execute(
            "INSERT INTO song_popularity (song_id, popularity_score, updated_at) VALUES (?, ?, ?)",
            (song_id, new_score, now),
        )
        cur.execute(
            "INSERT INTO song_popularity_events (song_id, source, boost, created_at) VALUES (?, ?, ?, ?)",
            (song_id, source, amount, now),
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


def get_current_popularity(song_id: int) -> float:
    """Return the latest popularity score for a song."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_schema(cur)
        cur.execute(
            "SELECT popularity_score FROM song_popularity WHERE song_id=? ORDER BY updated_at DESC LIMIT 1",
            (song_id,),
        )
        row = cur.fetchone()
        return float(row[0]) if row else 0.0


def get_last_boost_source(song_id: int) -> Optional[str]:
    """Return the source of the most recent popularity boost."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        _ensure_schema(cur)
        cur.execute(
            "SELECT source FROM song_popularity_events WHERE song_id=? ORDER BY id DESC LIMIT 1",
            (song_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None

