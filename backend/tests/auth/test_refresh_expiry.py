import sqlite3
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from backend.auth.service import AuthService


def test_refresh_token_expired(tmp_path):
    db_path = tmp_path / "auth.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE refresh_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            issued_at TEXT,
            expires_at TEXT NOT NULL,
            revoked_at TEXT,
            user_agent TEXT,
            ip TEXT
        )"""
    )
    conn.commit()

    svc = AuthService(db_path=str(db_path))
    token = "expiredtoken"
    token_hash = svc._hash_refresh(token)
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    conn.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (?,?,?)",
        (1, token_hash, past),
    )
    conn.commit()
    conn.close()

    with pytest.raises(ValueError) as exc:
        asyncio.run(svc.refresh(token))
    assert str(exc.value) == "REFRESH_EXPIRED"
