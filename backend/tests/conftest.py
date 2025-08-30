import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

import pytest

try:  # pragma: no cover - fastapi is optional for some test suites
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from httpx import AsyncClient
except Exception:  # pragma: no cover
    FastAPI = None  # type: ignore
    TestClient = None  # type: ignore
    AsyncClient = None  # type: ignore

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.db import get_conn
from auth.service import AuthService

try:  # pragma: no cover - optional in minimal test runs
    from routes import payment_routes
    from services.economy_service import EconomyService
    from services.payment_service import PaymentService
except Exception:  # pragma: no cover
    payment_routes = None  # type: ignore
    EconomyService = None  # type: ignore
    PaymentService = None  # type: ignore

@pytest.fixture(scope="session")
def db_path(tmp_path_factory, monkeypatch):
    db_file = tmp_path_factory.mktemp("db") / "test.db"
    os.environ["ROCKMUNDO_DB_PATH"] = str(db_file)
    import utils.db as db_module
    db_module.DEFAULT_DB = str(db_file)
    with get_conn(str(db_file)) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              display_name TEXT,
              is_active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT DEFAULT (datetime('now')),
              updated_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, description TEXT);
            CREATE TABLE IF NOT EXISTS user_roles (user_id INTEGER NOT NULL, role_id INTEGER NOT NULL, PRIMARY KEY (user_id, role_id));
            CREATE TABLE IF NOT EXISTS refresh_tokens (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              token_hash TEXT NOT NULL,
              issued_at TEXT DEFAULT (datetime('now')),
              expires_at TEXT NOT NULL,
              revoked_at TEXT,
              user_agent TEXT,
              ip TEXT
            );
            CREATE TABLE IF NOT EXISTS access_tokens (
              jti TEXT PRIMARY KEY,
              user_id INTEGER NOT NULL,
              expires_at TEXT NOT NULL,
              revoked_at TEXT
            );
            CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT NOT NULL, meta JSON, created_at TEXT DEFAULT (datetime('now')));
            INSERT OR IGNORE INTO roles (id, name) VALUES (1,'admin'),(2,'moderator'),(3,'band_member'),(4,'user');
            """
        )
    # patch services to use this db
    from auth import routes as auth_routes
    auth_routes.svc = AuthService(str(db_file))
    if EconomyService and PaymentService and payment_routes:
        economy = EconomyService(str(db_file))
        economy.ensure_schema()
        payment_routes._economy = economy
        payment_routes.svc = PaymentService(payment_routes._gateway, economy)
    return str(db_file)

@pytest.fixture
def client(db_path):
    if FastAPI is None or TestClient is None:
        pytest.skip("FastAPI not installed")
    from auth.routes import router as auth_router
    from routes import event_routes, payment_routes

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(event_routes.router)
    app.include_router(payment_routes.router)
    return TestClient(app)


@pytest.fixture
def client_factory():
    if FastAPI is None or TestClient is None:
        pytest.skip("FastAPI not installed")

    def _client(app: FastAPI, overrides: dict | None = None) -> TestClient:
        overrides = overrides or {}
        for dep, override in overrides.items():
            app.dependency_overrides[dep] = override
        return TestClient(app)

    return _client


@pytest.fixture
def async_client_factory():
    if FastAPI is None or AsyncClient is None:
        pytest.skip("FastAPI not installed")

    @asynccontextmanager
    async def _client(app: FastAPI, overrides: dict | None = None):
        overrides = overrides or {}
        for dep, override in overrides.items():
            app.dependency_overrides[dep] = override
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    return _client
