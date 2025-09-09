import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import sys


import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import backend.auth as backend_auth
import backend.core as backend_core
sys.modules.setdefault("auth", backend_auth)
sys.modules.setdefault("core", backend_core)

from backend.auth.service import AuthService


def test_refresh_handles_timezone(tmp_path, monkeypatch):
    db = tmp_path / "auth.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE refresh_tokens (
            user_id INTEGER,
            token_hash TEXT PRIMARY KEY,
            expires_at TEXT,
            revoked_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE audit_log (
            user_id INTEGER,
            action TEXT,
            meta TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    svc = AuthService(str(db))
    token = "refresh-token"
    token_hash = svc._hash_refresh(token)
    expires_at = "2023-09-30T00:00:00-05:00"  # 5 hours behind UTC

    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (1, ?, ?)",
        (token_hash, expires_at),
    )
    conn.commit()
    conn.close()

    async def fake_make_access_token(user_id: int) -> str:
        return "access"

    async def fake_new_refresh_token(user_id: int, user_agent: str = "", ip: str = ""):
        return {"refresh_token": "new", "expires_at": "2030-01-01T00:00:00+00:00"}

    svc._make_access_token = fake_make_access_token
    svc._new_refresh_token = fake_new_refresh_token

    monkeypatch.setattr(
        "backend.auth.service._now", lambda: datetime(2023, 9, 30, 2, tzinfo=timezone.utc)
    )

    result = asyncio.run(svc.refresh(token))
    assert result["access_token"] == "access"

