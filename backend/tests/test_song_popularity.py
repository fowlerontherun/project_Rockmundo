import sqlite3
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.database import DB_PATH
from backend.routes.music_metrics_routes import router as metrics_router
from backend.services.song_popularity_service import (
    add_event,
    apply_decay,
    get_history,
    HALF_LIFE_DAYS,
)


def _reset_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS song_popularity")
        cur.execute("DROP TABLE IF EXISTS song_popularity_events")
        conn.commit()


def test_add_event_and_decay():
    _reset_db()
    add_event(1, 10, "stream")
    add_event(1, 5, "sale")
    hist = get_history(1)
    assert hist[-1]["popularity_score"] == 15
    apply_decay()
    hist2 = get_history(1)
    assert len(hist2) == 3
    assert hist2[-1]["popularity_score"] < 15


def test_popularity_endpoint():
    _reset_db()
    add_event(2, 3, "stream")
    app = FastAPI()
    app.include_router(metrics_router)
    client = TestClient(app)
    resp = client.get("/music/metrics/songs/2/popularity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["song_id"] == 2
    assert data["current_popularity"] == 3
    assert data["half_life_days"] == HALF_LIFE_DAYS
    assert data["last_boost_source"] == "stream"
    assert len(data["history"]) == 1
