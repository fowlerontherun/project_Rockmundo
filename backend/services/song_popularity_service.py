import sqlite3
from typing import Optional, List, Dict

from backend.database import DB_PATH


class SongPopularityService:
    """Track song popularity boosts from various media events."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH

    def add_event(self, song_id: int, source: str, boost: int) -> Dict[str, int]:
        """Apply a popularity boost and log the event.

        Returns the new popularity score for the song.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO song_popularity_events (song_id, source, boost)
            VALUES (?, ?, ?)
            """,
            (song_id, source, boost),
        )
        cur.execute(
            """
            INSERT INTO song_popularity (song_id, score)
            VALUES (?, ?)
            ON CONFLICT(song_id) DO UPDATE SET score = score + excluded.score
            """,
            (song_id, boost),
        )
        cur.execute(
            "SELECT score FROM song_popularity WHERE song_id = ?",
            (song_id,),
        )
        row = cur.fetchone()
        conn.commit()
        conn.close()
        return {"song_id": song_id, "score": int(row[0] if row else 0)}

    def list_events(self, song_id: Optional[int] = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        if song_id is None:
            cur.execute(
                "SELECT id, song_id, source, boost, created_at FROM song_popularity_events ORDER BY id DESC"
            )
        else:
            cur.execute(
                """
                SELECT id, song_id, source, boost, created_at
                FROM song_popularity_events
                WHERE song_id = ?
                ORDER BY id DESC
                """,
                (song_id,),
            )
        rows = cur.fetchall()
        conn.close()
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
