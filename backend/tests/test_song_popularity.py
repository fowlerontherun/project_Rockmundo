import sqlite3

import pytest

try:  # pragma: no cover - FastAPI optional in some test suites
    from fastapi import FastAPI
except Exception:  # pragma: no cover
    FastAPI = None  # type: ignore

from backend.database import DB_PATH
from backend.services import song_popularity_service
from backend.services.song_popularity_service import (
    HALF_LIFE_DAYS,
    add_event,
    apply_decay,
    get_history,
)


def _reset_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS song_popularity")
        cur.execute("DROP TABLE IF EXISTS song_popularity_events")
        cur.execute("DROP TABLE IF EXISTS song_popularity_forecasts")
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
    data = {
        "song_id": 2,
        "current_popularity": song_popularity_service.get_current_popularity(2),
        "half_life_days": HALF_LIFE_DAYS,
        "last_boost_source": song_popularity_service.get_last_boost_source(2),
        "history": song_popularity_service.get_history(2),
        "breakdown": song_popularity_service.get_breakdown(2),
    }
    assert data["song_id"] == 2
    assert data["current_popularity"] == 3
    assert data["half_life_days"] == HALF_LIFE_DAYS
    assert data["last_boost_source"] == "stream"
    assert len(data["history"]) == 1
    assert data["breakdown"]["global"]["any"] == 3


def test_regional_breakdown():
    _reset_db()
    add_event(3, 5, "stream", region_code="US", platform="spotify")
    add_event(3, 2, "stream", region_code="EU", platform="apple")
    data = {
        "breakdown": song_popularity_service.get_breakdown(3)
    }
    assert data["breakdown"]["US"]["spotify"] == 5
    assert data["breakdown"]["EU"]["apple"] == 2


def test_forecast_generation():
    _reset_db()
    add_event(4, 10, "stream")
    add_event(4, 5, "sale")
    from backend.services.song_popularity_forecast import forecast_service

    forecasts = forecast_service.forecast_song(4, days=3)
    assert len(forecasts) == 3
    assert "predicted_score" in forecasts[0]


def test_forecast_endpoint(client_factory):
    if FastAPI is None:
        pytest.skip("FastAPI not installed")
    _reset_db()
    app = FastAPI()
    from backend.routes.song_forecast_routes import router as forecast_router

    app.include_router(forecast_router)
    add_event(6, 5, "stream")
    add_event(6, 3, "sale")
    client = client_factory(app)
    resp = client.get("/songs/6/forecast")
    assert resp.status_code == 200
    data = resp.json()
    assert data["song_id"] == 6
    assert len(data["forecast"]) > 0
    assert "predicted_score" in data["forecast"][0]


def test_add_event_invalid_inputs():
    _reset_db()
    with pytest.raises(ValueError):
        add_event(1, 5, "stream", region_code="XX")
    with pytest.raises(ValueError):
        add_event(1, 5, "stream", platform="unknown")


def test_get_song_popularity_validation(client_factory):
    if FastAPI is None:
        pytest.skip("FastAPI not installed")
    _reset_db()
    app = FastAPI()
    from backend.routes import music_metrics_routes

    app.include_router(music_metrics_routes.router)
    client = client_factory(app)

    # valid request
    song_popularity_service.add_event(
        1, "stream", 5, region_code="US", platform="spotify"
    )
    resp = client.get(
        "/music/metrics/songs/1/popularity?region_code=US&platform=spotify"
    )
    assert resp.status_code == 200

    # invalid region
    resp = client.get(
        "/music/metrics/songs/1/popularity?region_code=XX&platform=spotify"
    )
    assert resp.status_code == 400

    # invalid platform
    resp = client.get(
        "/music/metrics/songs/1/popularity?region_code=US&platform=bad"
    )
    assert resp.status_code == 400


def test_date_filters():
    _reset_db()
    add_event(5, 5, "stream", region_code="US", platform="spotify")
    add_event(5, 3, "stream", region_code="US", platform="spotify")
    add_event(5, 4, "stream", region_code="EU", platform="apple")
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE song_popularity SET updated_at=? WHERE id=1", ("2023-01-01T00:00:00",))
        cur.execute("UPDATE song_popularity SET updated_at=? WHERE id=2", ("2023-02-01T00:00:00",))
        cur.execute("UPDATE song_popularity SET updated_at=? WHERE id=3", ("2023-03-01T00:00:00",))
        conn.commit()
    hist = song_popularity_service.get_history(
        5, region_code="US", platform="spotify", start_date="2023-02-01T00:00:00"
    )
    assert len(hist) == 1
    assert hist[0]["popularity_score"] == 8
    breakdown = song_popularity_service.get_breakdown(
        5, start_date="2023-02-15T00:00:00", end_date="2023-03-15T00:00:00"
    )
    assert breakdown == {"EU": {"apple": 4}}
