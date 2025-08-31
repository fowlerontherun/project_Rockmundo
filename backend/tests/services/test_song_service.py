import sqlite3

from backend.services.song_service import SongService


def setup_db(path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE songs (id INTEGER PRIMARY KEY AUTOINCREMENT, band_id INTEGER, title TEXT, duration_sec INTEGER, genre TEXT, play_count INTEGER, original_song_id INTEGER, license_fee INTEGER DEFAULT 0, royalty_rate REAL DEFAULT 0.0)"
    )
    cur.execute(
        "CREATE TABLE royalties (id INTEGER PRIMARY KEY AUTOINCREMENT, song_id INTEGER, user_id INTEGER, percent INTEGER)"
    )
    cur.execute(
        "CREATE TABLE cover_royalties (id INTEGER PRIMARY KEY AUTOINCREMENT, song_id INTEGER, cover_band_id INTEGER, amount_owed INTEGER, amount_paid INTEGER, license_proof_url TEXT)"
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


def test_cover_royalties_and_license(tmp_path):
    db_path = tmp_path / "songs.db"
    setup_db(db_path)
    service = SongService(db=str(db_path))

    original = {
        "band_id": 1,
        "title": "Original",
        "duration_sec": 120,
        "genre": "rock",
        "royalties_split": {1: 100},
        "license_fee": 1000,
        "royalty_rate": 0.1,
    }
    song_id = service.create_song(original)["song_id"]

    band_id = 2

    # Performing a cover without license should alert
    try:
        service.record_cover_usage(song_id, band_id, revenue_cents=1000)
        assert False, "expected PermissionError"
    except PermissionError:
        pass

    # Purchase license and record usage
    service.purchase_cover_license(song_id, band_id, "proof.png")
    res = service.record_cover_usage(song_id, band_id, revenue_cents=1000)
    assert res["amount_owed"] == 100
