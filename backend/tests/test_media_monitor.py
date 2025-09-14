import sqlite3

from backend.database import DB_PATH
from services.media_monitor_service import MediaMonitorService
import backend.services.song_popularity_service as sp_module
from services.song_popularity_service import song_popularity_service


def _reset_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS song_popularity")
        cur.execute("DROP TABLE IF EXISTS song_popularity_events")
        cur.execute("DROP TABLE IF EXISTS song_popularity_forecasts")
        conn.commit()


def test_poll_and_adjust():
    _reset_db()
    feed = lambda: ["Breaking news song_id:42"]
    svc = MediaMonitorService(feed_source=feed, default_boost=7)
    svc.poll_feed()
    assert sp_module.get_current_popularity(42) == 7
    events = song_popularity_service.list_events(song_id=42)
    assert events[0]["details"].startswith("Breaking news")
    svc.manual_adjust(42, -2, "correction")
    assert sp_module.get_current_popularity(42) == 5
