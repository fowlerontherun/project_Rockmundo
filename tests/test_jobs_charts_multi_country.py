import sys
import types
import sqlite3
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "backend"))

# Stub heavy dependencies before importing routes
auth_deps = types.ModuleType("backend.auth.dependencies")
auth_deps.get_current_user_id = lambda req=None: 1
sys.modules["backend.auth.dependencies"] = auth_deps

chart_service_stub = types.ModuleType("backend.services.chart_service")
chart_service_stub.calculate_weekly_chart = lambda *a, **k: {}
chart_service_stub.get_chart = lambda *a, **k: []
sys.modules["backend.services.chart_service"] = chart_service_stub

from backend import database
from backend.services.jobs_charts import ChartsJobsService
from backend.routes import chart_routes

def _setup_db(tmp_path):
    db = tmp_path / "charts.sqlite"
    database.DB_PATH = str(db)
    chart_routes.DB_PATH = str(db)
    svc = ChartsJobsService(db_path=str(db))
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute("CREATE TABLE songs (id INTEGER PRIMARY KEY, band_id INTEGER, title TEXT)")
        cur.execute(
            """
            CREATE TABLE streams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_id INTEGER,
                user_id INTEGER,
                country_code TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()
    return db, svc


def test_multi_country_stream_charts(tmp_path):
    db, svc = _setup_db(tmp_path)
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.executemany(
            "INSERT INTO songs (id, band_id, title) VALUES (?, ?, ?)",
            [(1, 1, "Song A"), (2, 1, "Song B")],
        )
        for _ in range(60):
            cur.execute(
                "INSERT INTO streams (song_id, user_id, country_code, created_at) VALUES (1, 1, 'US', '2024-01-01 00:00:00')"
            )
        for _ in range(5):
            cur.execute(
                "INSERT INTO streams (song_id, user_id, country_code, created_at) VALUES (1, 2, 'US', '2024-01-01 00:00:00')"
            )
        for _ in range(30):
            cur.execute(
                "INSERT INTO streams (song_id, user_id, country_code, created_at) VALUES (2, 3, 'US', '2024-01-01 00:00:00')"
            )
        for _ in range(10):
            cur.execute(
                "INSERT INTO streams (song_id, user_id, country_code, created_at) VALUES (1, 4, 'UK', '2024-01-01 00:00:00')"
            )
        for _ in range(40):
            cur.execute(
                "INSERT INTO streams (song_id, user_id, country_code, created_at) VALUES (2, 5, 'UK', '2024-01-01 00:00:00')"
            )
        conn.commit()
    svc.run_daily("2024-01-01")
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT country_code, rank, work_id, metric_value
            FROM chart_snapshots
            WHERE chart_type='streams_song' AND period='daily'
            ORDER BY country_code, rank
            """
        )
        rows = cur.fetchall()
    assert rows == [
        ("UK", 1, 2, 40.0),
        ("UK", 2, 1, 10.0),
        ("US", 1, 1, 55.0),
        ("US", 2, 2, 30.0),
    ]

    app = FastAPI()
    app.include_router(chart_routes.router)
    client = TestClient(app)
    resp = client.get("/charts/US", params={"chart_type": "streams_song", "period": "daily"})
    assert resp.status_code == 200
    assert [r["work_id"] for r in resp.json()] == [1, 2]
