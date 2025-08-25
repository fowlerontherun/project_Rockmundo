# File: backend/tests/test_auth_flow.py
from fastapi import FastAPI
from fastapi.testclient import TestClient
from utils.db import get_conn
from auth.routes import router as auth_router

def make_app():
    app = FastAPI()
    app.include_router(auth_router)
    return app

def setup_db():
    # minimal schema from migration (subset)
    from pathlib import Path
    with get_conn() as conn:
        conn.executescript("""
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
        CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT NOT NULL, meta JSON, created_at TEXT DEFAULT (datetime('now')));
        INSERT OR IGNORE INTO roles (id, name) VALUES (1,'admin'),(2,'moderator'),(3,'band_member'),(4,'user');
        """)

def test_register_login_refresh_me_logout():
    setup_db()
    app = make_app()
    c = TestClient(app)

    # Register
    r = c.post("/auth/register", json={"email":"test@example.com","password":"Secretpass1","display_name":"Tester"})
    assert r.status_code == 200
    uid = r.json()["id"]

    # Login
    r = c.post("/auth/login", json={"email":"test@example.com","password":"Secretpass1"})
    assert r.status_code == 200
    data = r.json()
    at = data["access_token"]; rt = data["refresh_token"]
    assert at and rt

    # Me
    headers = {"Authorization": f"Bearer {at}"}
    r = c.get("/auth/me", headers=headers)
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == "test@example.com"
    assert "user" in me["roles"]

    # Refresh
    r = c.post("/auth/refresh", json={"refresh_token": rt})
    assert r.status_code == 200
    at2 = r.json()["access_token"]
    assert at2 and at2 != at

    # Logout (revoke current refresh)
    r = c.post("/auth/logout", json={"refresh_token": rt})
    assert r.status_code == 200

    # Refresh with revoked should fail
    r = c.post("/auth/refresh", json={"refresh_token": rt})
    assert r.status_code == 401
