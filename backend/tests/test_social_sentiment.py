import sqlite3

from backend.database import DB_PATH
from services.social_sentiment_service import SocialSentimentService
from services.song_popularity_service import get_current_popularity


def _reset_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS song_sentiment_history")
        cur.execute("DROP TABLE IF EXISTS song_popularity")
        cur.execute("DROP TABLE IF EXISTS song_popularity_events")
        conn.commit()


def test_sentiment_processing_updates_popularity():
    _reset_db()
    svc = SocialSentimentService(fetcher=lambda song_id: 0.8)
    result = svc.process_song(1)
    assert result["boost"] == 8
    assert get_current_popularity(1) == 8
    history = svc.history(1)
    assert len(history) == 1
    assert history[0]["sentiment"] == 0.8
