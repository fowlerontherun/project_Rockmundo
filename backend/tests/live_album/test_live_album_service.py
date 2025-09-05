import json
import sqlite3

import pytest

from backend.services import audio_mixing_service
from backend.services.live_album_service import LiveAlbumService


def _insert_performance(cur, band_id, setlist, skill_gain, city="", venue=""):
    cur.execute(
        """
        INSERT INTO live_performances (
            band_id, city, venue, date, setlist, crowd_size, fame_earned,
            revenue_earned, skill_gain, merch_sold
        ) VALUES (?, ?, ?, '', ?, 0, 0, 0, ?, 0)
        """,
        (band_id, city, venue, json.dumps(setlist), skill_gain),
    )


def test_compile_live_album(tmp_path, monkeypatch):
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
        _insert_performance(cur, 1, setlist, 0.0, f"City {idx}", f"Venue {idx}")
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

    called = {}

    def fake_mix(ids):
        called["ids"] = ids
        return [pid + 1000 for pid in ids]

    monkeypatch.setattr(audio_mixing_service, "mix_tracks", fake_mix)

    service = LiveAlbumService(str(db_file))
    album = service.compile_live_album([1, 2, 3, 4, 5], "Best Live")

    assert album["album_type"] == "live"
    assert [s["song_id"] for s in album["songs"]] == [1, 2]
    # Performance 5 has highest score (80)
    assert all(s["show_id"] == 5 for s in album["songs"])
    assert all(s["performance_score"] == 80 for s in album["songs"])
    assert called["ids"] == [5, 5]
    assert all("performance_id" not in t for t in album["tracks"])
    assert all(t["show_id"] == 5 for t in album["tracks"])
    assert all(t["performance_score"] == 80 for t in album["tracks"])
    assert all(t["track_id"] == 1005 for t in album["tracks"])
    assert album["cover_art"]


def test_publish_album_records_show_data(tmp_path, monkeypatch):
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
        _insert_performance(cur, 1, setlist, 0.0, f"City {idx}", f"Venue {idx}")
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

    monkeypatch.setattr(
        audio_mixing_service,
        "mix_tracks",
        lambda ids: [pid + 1000 for pid in ids],
    )

    service = LiveAlbumService(str(db_file))
    album = service.compile_live_album([1, 2, 3, 4, 5], "Best Live")
    release_id = service.publish_album(album["id"])

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(
        "SELECT song_id, show_id, performance_score FROM release_tracks WHERE release_id = ?",
        (release_id,),
    )
    rows = cur.fetchall()
    conn.close()

    assert len(rows) == 2
    assert all(row[1] == 5 for row in rows)
    assert all(row[2] == 80 for row in rows)

def test_update_tracks_validation(tmp_path):
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
    # Tables tracking existing releases for validation
    cur.execute(
        "CREATE TABLE releases (id INTEGER PRIMARY KEY AUTOINCREMENT, format TEXT)"
    )
    cur.execute(
        "CREATE TABLE release_tracks (release_id INTEGER, song_id INTEGER, show_id INTEGER, performance_score REAL)"
    )

    setlist = {"setlist": [{"type": "song", "reference": "1"}, {"type": "song", "reference": "2"}], "encore": []}
    for idx in range(1, 6):
        _insert_performance(cur, 1, setlist, 0.0, f"City {idx}", f"Venue {idx}")
        cur.execute(
            "INSERT INTO recorded_tracks (performance_id, song_id, performance_score, created_at) VALUES (?, 1, ?, '')",
            (idx, 50),
        )
        cur.execute(
            "INSERT INTO recorded_tracks (performance_id, song_id, performance_score, created_at) VALUES (?, 2, ?, '')",
            (idx, 60),
        )
    # Mark song 1 as already released as a single
    cur.execute("INSERT INTO releases (format) VALUES ('single')")
    release_id = cur.lastrowid
    cur.execute(
        "INSERT INTO release_tracks (release_id, song_id) VALUES (?, 1)",
        (release_id,),
    )
    conn.commit()
    conn.close()

    service = LiveAlbumService(str(db_file))
    album = service.compile_live_album([1, 2, 3, 4, 5], "Best Live")
    album_id = album["id"]

    # Reorder tracks
    updated = service.update_tracks(album_id, [2, 1])
    assert updated["song_ids"] == [2, 1]

    # Removing a track released as a single should fail
    with pytest.raises(ValueError):
        service.update_tracks(album_id, [2])

    # Removing an unreleased track succeeds
    updated = service.update_tracks(album_id, [1])
    assert updated["song_ids"] == [1]


def test_compile_live_album_missing_recordings(tmp_path):
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
    for idx in range(1, 6):
        _insert_performance(cur, 1, setlist, 0.0)
        cur.execute(
            "INSERT INTO recorded_tracks (performance_id, song_id, performance_score, created_at) VALUES (?, 1, ?, '')",
            (idx, 10),
        )
        if idx != 4:
            cur.execute(
                "INSERT INTO recorded_tracks (performance_id, song_id, performance_score, created_at) VALUES (?, 2, ?, '')",
                (idx, 10),
            )
    conn.commit()
    conn.close()

    service = LiveAlbumService(str(db_file))
    with pytest.raises(ValueError) as exc:
        service.compile_live_album([1, 2, 3, 4, 5], "Best Live")
    assert "4" in str(exc.value)
    assert "2" in str(exc.value)

