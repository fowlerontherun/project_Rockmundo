import sqlite3

from backend.services.song_service import SongService


def setup_db(path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE songs (id INTEGER PRIMARY KEY AUTOINCREMENT, band_id INTEGER, title TEXT, duration_sec INTEGER, genre TEXT, play_count INTEGER, original_song_id INTEGER)"
    )
    cur.execute(
        "CREATE TABLE royalties (id INTEGER PRIMARY KEY AUTOINCREMENT, song_id INTEGER, user_id INTEGER, percent INTEGER)"
    )
    conn.commit()
    conn.close()


def test_create_cover_and_list(tmp_path):
    db_path = tmp_path / "songs.db"
    setup_db(db_path)
    service = SongService(db=str(db_path))

    original = {
        "band_id": 1,
        "title": "Original",
        "duration_sec": 120,
        "genre": "rock",
        "royalties_split": {1: 100},
    }
    res = service.create_song(original)
    orig_id = res["song_id"]

    cover = {
        "band_id": 2,
        "title": "Cover",
        "duration_sec": 120,
        "genre": "rock",
        "royalties_split": {2: 100},
        "original_song_id": orig_id,
    }
    service.create_song(cover)

    covers = service.list_covers_of_song(orig_id)
    assert len(covers) == 1
    assert covers[0]["band_id"] == 2
