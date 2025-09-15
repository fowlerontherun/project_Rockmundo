import sqlite3
from datetime import datetime
from typing import Callable, Dict, List, Optional
from database import DB_PATH
from backend.services.song_popularity_service import add_event

def _ensure_schema(cur: sqlite3.Cursor) -> None:
    """Ensure sentiment history table exists."""
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS song_sentiment_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            sentiment REAL NOT NULL,
            captured_at TEXT NOT NULL
        )
        """
    )


class SocialSentimentService:
    """Fetch social sentiment scores and map them to popularity boosts."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        fetcher: Optional[Callable[[int], float]] = None,
    ) -> None:
        self.db_path = db_path or DB_PATH
        # Fetcher returns a sentiment score (e.g., -1.0..1.0 or 0..1).
        # Default fetcher returns neutral sentiment.
        self.fetcher = fetcher or (lambda song_id: 0.0)

    def fetch_sentiment(self, song_id: int) -> float:
        """Fetch sentiment score for a song from the configured fetcher."""
        return float(self.fetcher(song_id))

    def process_song(self, song_id: int) -> Dict[str, float]:
        """Fetch sentiment, log it, and convert to popularity boost."""
        score = self.fetch_sentiment(song_id)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            _ensure_schema(cur)
            now = datetime.utcnow().isoformat()
            cur.execute(
                """
                INSERT INTO song_sentiment_history (song_id, sentiment, captured_at)
                VALUES (?, ?, ?)
                """,
                (song_id, score, now),
            )
            conn.commit()
        # Translate sentiment score to a boost (simple linear mapping)
        boost = int(round(score * 10))
        if boost:
            add_event(song_id, boost, source="social_sentiment")
        return {"song_id": song_id, "sentiment": score, "boost": boost}

    def history(self, song_id: int, limit: int = 100) -> List[Dict[str, float]]:
        """Return sentiment history for a song."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            _ensure_schema(cur)
            cur.execute(
                """
                SELECT sentiment, captured_at
                FROM song_sentiment_history
                WHERE song_id=?
                ORDER BY id DESC
                LIMIT ?
                """,
                (song_id, limit),
            )
            rows = cur.fetchall()
        # Return in chronological order
        return [dict(r) for r in reversed(rows)]


# Singleton instance used elsewhere
social_sentiment_service = SocialSentimentService()
