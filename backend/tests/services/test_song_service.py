import sqlite3

import pytest

from backend.services.song_service import SongService
from backend.jobs.royalty_clearing_job import run as royalty_run


def setup_db(path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE songs (id INTEGER PRIMARY KEY AUTOINCREMENT, band_id INTEGER, title TEXT, duration_sec INTEGER, genre TEXT, play_count INTEGER, original_song_id INTEGER, license_fee INTEGER DEFAULT 0, royalty_rate REAL DEFAULT 0.0, legacy_state TEXT DEFAULT 'new', original_release_date TEXT)"
    )
    cur.execute(
        "CREATE TABLE royalties (id INTEGER PRIMARY KEY AUTOINCREMENT, song_id INTEGER, user_id INTEGER, percent INTEGER)"
    )
    cur.execute(
        "CREATE TABLE cover_royalties (id INTEGER PRIMARY KEY AUTOINCREMENT, song_id INTEGER, cover_band_id INTEGER, amount_owed INTEGER, amount_paid INTEGER)"
    )
    cur.execute(
        "CREATE TABLE cover_license_transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, song_id INTEGER, cover_band_id INTEGER, license_fee INTEGER, license_proof_url TEXT, purchased_at TEXT, expires_at TEXT)"
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

    cover_band = 2
    cover = {
        "band_id": cover_band,
        "title": "Cover",
        "duration_sec": 120,
        "genre": "rock",
        "royalties_split": {cover_band: 100},
        "original_song_id": orig_id,
    }

    # creating a cover without a license should fail
    try:
        service.create_cover(cover, license_transaction_id=999)
        assert False, "expected PermissionError"
    except PermissionError:
        pass

    tx = service.purchase_cover_license(orig_id, cover_band, "proof.png")
    service.create_cover(cover, tx["transaction_id"])

    covers = service.list_covers_of_song(orig_id)
    assert len(covers) == 1
    assert covers[0]["band_id"] == cover_band


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

    # Purchase license and create cover
    tx = service.purchase_cover_license(song_id, band_id, "proof.png")
    cover_data = {
        "band_id": band_id,
        "title": "Cover",
        "duration_sec": 120,
        "genre": "rock",
        "royalties_split": {band_id: 100},
        "original_song_id": song_id,
    }
    service.create_cover(cover_data, tx["transaction_id"])

    # Record usage and check royalties
    res = service.record_cover_usage(song_id, band_id, revenue_cents=1000)
    assert res["amount_owed"] == 100
    royalties = service.list_cover_royalties(band_id)
    assert len(royalties) == 1

    # Run royalty clearing job and ensure amount_paid updated
    royalty_run(db=str(db_path))
    royalties_after = service.list_cover_royalties(band_id)
    assert royalties_after[0]["amount_paid"] == royalties_after[0]["amount_owed"]


def test_update_song_rejects_disallowed_field(tmp_path):
    db_path = tmp_path / "songs.db"
    setup_db(db_path)
    service = SongService(db=str(db_path))

    song = {
        "band_id": 1,
        "title": "Test",
        "duration_sec": 120,
        "genre": "rock",
        "royalties_split": {1: 100},
    }
    song_id = service.create_song(song)["song_id"]

    with pytest.raises(ValueError):
        service.update_song(song_id, {"hack": "value"})
