import asyncio

import pytest
import utils.db as db_utils
from backend.auth.service import AuthService
from fastapi import HTTPException, Request
from utils.db import get_conn

from auth.dependencies import get_current_user_id, require_permission
from backend.services.analytics_service import SERVICE_LATENCY_MS, AnalyticsService
from backend.utils.metrics import generate_latest

DDL = """
CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT);
CREATE TABLE roles(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT);
CREATE TABLE user_roles(user_id INTEGER, role_id INTEGER, PRIMARY KEY(user_id, role_id));
CREATE TABLE transactions(id INTEGER PRIMARY KEY AUTOINCREMENT, amount_cents INTEGER, created_at TEXT);
CREATE TABLE active_events(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, event_id INTEGER, start_date TEXT, duration_days INTEGER);
CREATE TABLE skill_progress(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, skill TEXT, amount INTEGER, created_at TEXT);
CREATE TABLE access_tokens(
  jti TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  expires_at TEXT NOT NULL,
  revoked_at TEXT
);
"""


def setup_db(path: str) -> AuthService:
    with get_conn(path) as conn:
        conn.executescript(DDL)
        conn.executemany("INSERT INTO roles(id,name) VALUES (?,?)", [(1, "admin"), (2, "user")])
        conn.executemany("INSERT INTO users(id,username) VALUES (?,?)", [(1, "admin"), (2, "player")])
        conn.executemany("INSERT INTO user_roles(user_id,role_id) VALUES (?,?)", [(1,1), (2,2)])
        conn.executemany(
            "INSERT INTO transactions(amount_cents, created_at) VALUES (?,?)",
            [(100, "2024-01-01"), (200, "2024-01-02")],
        )
        conn.executemany(
            "INSERT INTO active_events(user_id,event_id,start_date,duration_days) VALUES (?,?,?,?)",
            [(1, 1, "2024-01-01", 1), (1, 1, "2024-01-02", 1), (2, 1, "2024-01-02", 1)],
        )
        conn.executemany(
            "INSERT INTO skill_progress(user_id,skill,amount,created_at) VALUES (?,?,?,?)",
            [
                (1, "guitar", 5, "2024-01-01"),
                (1, "guitar", 8, "2024-01-01"),
                (2, "vocals", 10, "2024-01-02"),
            ],
        )
    return AuthService(path)


def token(user_id: int, svc: AuthService) -> str:
    return asyncio.run(svc._make_access_token(user_id))


def test_metrics_and_permissions(tmp_path):
    db = str(tmp_path / "analytics.db")
    auth_svc = setup_db(db)
    db_utils.DEFAULT_DB = db
    svc = AnalyticsService(db_path=db)

    # metrics accuracy
    metrics = svc.time_series("2024-01-01", "2024-01-02")
    assert [m.dict() for m in metrics.economy] == [
        {"date": "2024-01-01", "value": 100},
        {"date": "2024-01-02", "value": 200},
    ]
    assert [m.dict() for m in metrics.events] == [
        {"date": "2024-01-01", "value": 1},
        {"date": "2024-01-02", "value": 2},
    ]
    assert [m.dict() for m in metrics.skills] == [
        {"date": "2024-01-01", "value": 13},
        {"date": "2024-01-02", "value": 10},
    ]

    # permission: missing token -> 401
    req = Request(headers={})
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user_id(req))
    assert exc.value.status_code == 401

    # permission: non-admin -> 403
    user_req = Request(headers={"Authorization": f"Bearer {token(2, auth_svc)}"})
    uid = asyncio.run(get_current_user_id(user_req))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(require_permission(["admin"], user_id=uid))
    assert exc.value.status_code == 403

    # permission: admin succeeds
    admin_req = Request(headers={"Authorization": f"Bearer {token(1, auth_svc)}"})
    uid = asyncio.run(get_current_user_id(admin_req))
    assert asyncio.run(require_permission(["admin"], user_id=uid))


def test_kpis_latency_metric(tmp_path):
    db = str(tmp_path / "analytics.db")
    svc = AnalyticsService(db_path=db)
    before = SERVICE_LATENCY_MS._values.get(("analytics_service", "kpis"), {"count": 0})["count"]
    svc.kpis("2024-01-01", "2024-01-02")
    after = SERVICE_LATENCY_MS._values[("analytics_service", "kpis")]["count"]
    assert after == before + 1
    output = generate_latest().decode()
    assert 'service_latency_ms_count{service="analytics_service",operation="kpis"}' in output
