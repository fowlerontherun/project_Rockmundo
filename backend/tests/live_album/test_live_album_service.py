import json
import sqlite3

from backend.services.live_album_service import LiveAlbumService


def _insert_performance(cur, band_id, setlist, skill_gain):
    cur.execute(
        """
        INSERT INTO live_performances (
            band_id, city, venue, date, setlist, crowd_size, fame_earned,
            revenue_earned, skill_gain, merch_sold
        ) VALUES (?, '', '', '', ?, 0, 0, 0, ?, 0)
        """,
        (band_id, json.dumps(setlist), skill_gain),
    )


def test_compile_live_album(tmp_path):
    db_file = tmp_path / "perf.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE live_performances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            band_id INTEGER,
            city TEXT,
            venue TEXT,
            date TEXT,
            setlist TEXT,
            crowd_size INTEGER,
            fame_earned INTEGER,
            revenue_earned INTEGER,
            skill_gain REAL,
            merch_sold INTEGER
        )
        """,
    )
    cur.execute(
        """
        CREATE TABLE recorded_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            performance_id INTEGER,
            song_id INTEGER,
            performance_score REAL,
            created_at TEXT
        )
        """,
    )
    setlist = {
        "setlist": [
            {"type": "song", "reference": "1"},
            {"type": "song", "reference": "2"},
        ],
        "encore": [],
    }
    scores = [50, 60, 55, 40, 80]
    for idx, score in enumerate(scores, start=1):
        _insert_performance(cur, 1, setlist, 0.0)
        cur.execute(
            "INSERT INTO recorded_tracks (performance_id, song_id, performance_score, created_at) VALUES (?, 1, ?, '')",
            (idx, score),
        )
        cur.execute(
            "INSERT INTO recorded_tracks (performance_id, song_id, performance_score, created_at) VALUES (?, 2, ?, '')",
            (idx, score),
        )
    conn.commit()
    conn.close()

    service = LiveAlbumService(str(db_file))
    album = service.compile_live_album([1, 2, 3, 4, 5], "Best Live")

    assert album["album_type"] == "live"
    assert album["song_ids"] == [1, 2]
    # Performance 5 has highest score (80)
    assert all(t["performance_id"] == 5 for t in album["tracks"])

