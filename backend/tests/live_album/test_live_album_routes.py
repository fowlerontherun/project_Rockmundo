import json
import sqlite3

import pytest
from fastapi import FastAPI

from routes import live_album_routes
from backend.services import audio_mixing_service


def _insert_performance(cur, band_id, setlist, skill_gain, perf_score, city="", venue=""):
    cur.execute(
        """
        INSERT INTO live_performances (
            band_id, city, venue, date, setlist, crowd_size, fame_earned,
            revenue_earned, skill_gain, merch_sold, performance_score
        ) VALUES (?, ?, ?, '', ?, 0, 0, 0, ?, 0, ?)
        """,
        (band_id, city, venue, json.dumps(setlist), skill_gain, perf_score),
    )
    perf_id = cur.lastrowid
    cur.execute(
        "INSERT INTO recorded_tracks (performance_id, song_id, performance_score, created_at) VALUES (?, 1, ?, '')",
        (perf_id, perf_score),
    )
    cur.execute(
        "INSERT INTO recorded_tracks (performance_id, song_id, performance_score, created_at) VALUES (?, 2, ?, '')",
        (perf_id, perf_score),
    )


@pytest.mark.asyncio
async def test_compile_route(tmp_path, async_client_factory, monkeypatch):
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
            merch_sold INTEGER,
            performance_score REAL
        )
        """
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
        """
    )
    setlist = {"setlist": [{"type": "song", "reference": "1"}, {"type": "song", "reference": "2"}], "encore": []}
    scores = [50, 60, 55, 40, 80]
    for idx, score in enumerate(scores, start=1):
        _insert_performance(cur, 1, setlist, 0.0, score, f"City {idx}", f"Venue {idx}")
    conn.commit()
    conn.close()

    called: dict = {}

    def fake_mix(ids):
        called["ids"] = ids
        return [pid + 1000 for pid in ids]

    monkeypatch.setattr(audio_mixing_service, "mix_tracks", fake_mix)

    live_album_routes.service.db_path = str(db_file)
    app = FastAPI()
    app.include_router(live_album_routes.router, prefix="/api")

    async with async_client_factory(app) as client:
        resp = await client.post(
            "/api/live_albums/compile",
            json={"show_ids": [1, 2, 3, 4, 5], "album_title": "Best Live"},
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["song_ids"] == [1, 2]
        assert called["ids"] == [5, 5]
        assert all(t["track_id"] == 1005 for t in data["tracks"])
        assert all(t["show_id"] == 5 for t in data["tracks"])
        assert data["cover_art"]


@pytest.mark.asyncio
async def test_patch_tracks_route(tmp_path, async_client_factory):
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
            merch_sold INTEGER,
            performance_score REAL
        )
        """
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
        """
    )
    cur.execute(
        "CREATE TABLE releases (id INTEGER PRIMARY KEY AUTOINCREMENT, format TEXT)"
    )
    cur.execute(
        "CREATE TABLE release_tracks (release_id INTEGER, song_id INTEGER, show_id INTEGER, performance_score REAL)"
    )
    setlist = {"setlist": [{"type": "song", "reference": "1"}, {"type": "song", "reference": "2"}], "encore": []}
    scores = [50, 60, 55, 40, 80]
    for idx, score in enumerate(scores, start=1):
        _insert_performance(cur, 1, setlist, 0.0, score, f"City {idx}", f"Venue {idx}")
    cur.execute("INSERT INTO releases (format) VALUES ('single')")
    rid = cur.lastrowid
    cur.execute(
        "INSERT INTO release_tracks (release_id, song_id) VALUES (?, 1)", (rid,),
    )
    conn.commit()
    conn.close()

    live_album_routes.service.db_path = str(db_file)
    app = FastAPI()
    app.include_router(live_album_routes.router, prefix="/api")

    async with async_client_factory(app) as client:
        resp = await client.post(
            "/api/live_albums/compile",
            json={"show_ids": [1, 2, 3, 4, 5], "album_title": "Best Live"},
        )
        album_id = resp.json()["id"]

        resp = await client.patch(
            f"/api/live_albums/{album_id}/tracks", json={"track_ids": [2, 1]}
        )
        assert resp.status_code == 200
        assert resp.json()["song_ids"] == [2, 1]

        resp = await client.patch(
            f"/api/live_albums/{album_id}/tracks", json={"track_ids": [2]}
        )
        assert resp.status_code == 400

        resp = await client.patch(
            f"/api/live_albums/{album_id}/tracks", json={"track_ids": [1]}
        )
        assert resp.status_code == 200
        assert resp.json()["song_ids"] == [1]


@pytest.mark.asyncio
async def test_publish_route(tmp_path, async_client_factory, monkeypatch):
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
            merch_sold INTEGER,
            performance_score REAL
        )
        """
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
        """
    )
    setlist = {"setlist": [{"type": "song", "reference": "1"}, {"type": "song", "reference": "2"}], "encore": []}
    scores = [50, 60, 55, 40, 80]
    for idx, score in enumerate(scores, start=1):
        _insert_performance(cur, 1, setlist, 0.0, score, f"City {idx}", f"Venue {idx}")
    conn.commit()
    conn.close()

    def fake_mix(ids):
        return [pid + 1000 for pid in ids]

    monkeypatch.setattr(audio_mixing_service, "mix_tracks", fake_mix)

    live_album_routes.service.db_path = str(db_file)
    app = FastAPI()
    app.include_router(live_album_routes.router, prefix="/api")

    async with async_client_factory(app) as client:
        resp = await client.post(
            "/api/live_albums/compile",
            json={"show_ids": [1, 2, 3, 4, 5], "album_title": "Best Live"},
        )
        album_id = resp.json()["id"]

        resp = await client.post(f"/api/live_albums/{album_id}/publish")
        assert resp.status_code == 200
        published_id = resp.json()["album_id"]

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT title FROM releases WHERE id = ?", (published_id,))
    assert cur.fetchone() is not None
    cur.execute(
        "SELECT COUNT(*) FROM release_tracks WHERE release_id = ?", (published_id,)
    )
    assert cur.fetchone()[0] == 2
    conn.close()

