import json
import sqlite3

from fastapi import FastAPI

from backend.routes import live_album_routes


def _insert_performance(cur, band_id, setlist, skill_gain, perf_score):
    cur.execute(
        """
        INSERT INTO live_performances (
            band_id, city, venue, date, setlist, crowd_size, fame_earned,
            revenue_earned, skill_gain, merch_sold, performance_score
        ) VALUES (?, '', '', '', ?, 0, 0, 0, ?, 0, ?)
        """,
        (band_id, json.dumps(setlist), skill_gain, perf_score),
    )


def test_compile_route(tmp_path, client_factory):
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
    setlist = {"setlist": [{"type": "song", "reference": "1"}, {"type": "song", "reference": "2"}], "encore": []}
    scores = [50, 60, 55, 40, 80]
    for score in scores:
        _insert_performance(cur, 1, setlist, 0.0, score)
    conn.commit()
    conn.close()

    live_album_routes.service.db_path = str(db_file)
    app = FastAPI()
    app.include_router(live_album_routes.router, prefix="/api")
    client = client_factory(app)

    resp = client.post("/api/live_albums/compile", json={"show_ids": [1, 2, 3, 4, 5], "album_title": "Best Live"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["song_ids"] == [1, 2]
    assert all(t["performance_id"] == 5 for t in data["tracks"])
