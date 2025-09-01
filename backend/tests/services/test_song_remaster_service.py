import sqlite3

from backend.services.song_remaster_service import SongRemasterService
import backend.services.song_popularity_service as sp_module


def setup_db(path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            band_id INTEGER,
            title TEXT,
            duration_sec INTEGER,
            genre TEXT,
            play_count INTEGER,
            original_song_id INTEGER,
            license_fee INTEGER DEFAULT 0,
            royalty_rate REAL DEFAULT 0.0,
            legacy_state TEXT DEFAULT 'new',
            original_release_date TEXT
        );
        CREATE TABLE royalties (id INTEGER PRIMARY KEY AUTOINCREMENT, song_id INTEGER, user_id INTEGER, percent INTEGER);
        """
    )
    conn.commit()
    conn.close()


def test_remaster_creates_song(tmp_path):
    db = tmp_path / "songs.db"
    setup_db(db)
    orig_db = sp_module.DB_PATH
    orig_service_db = sp_module.song_popularity_service.db_path
    sp_module.DB_PATH = str(db)
    sp_module.song_popularity_service.db_path = str(db)

    svc = SongRemasterService(db_path=str(db))
    orig = {
        "band_id": 1,
        "title": "Hit",
        "duration_sec": 180,
        "genre": "rock",
        "royalties_split": {1: 100},
    }
    original_id = svc.song_service.create_song(orig)["song_id"]
    result = svc.remaster_song(original_id)
    assert "remaster_id" in result
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute("SELECT legacy_state FROM songs WHERE id=?", (original_id,))
        assert cur.fetchone()[0] == "classic"
    events = sp_module.song_popularity_service.list_events(result["remaster_id"], source="remaster_release")
    assert events
    sp_module.DB_PATH = orig_db
    sp_module.song_popularity_service.db_path = orig_service_db
