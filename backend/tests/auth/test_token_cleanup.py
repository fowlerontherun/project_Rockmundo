import sqlite3
from datetime import datetime, timedelta, timezone

from jobs import cleanup_tokens


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def _setup_db(path: str) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE access_tokens (
            jti TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            revoked_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE refresh_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            issued_at TEXT,
            expires_at TEXT NOT NULL,
            revoked_at TEXT,
            user_agent TEXT,
            ip TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def test_cleanup_removes_expired_and_revoked_tokens(tmp_path, monkeypatch):
    db_path = tmp_path / "tokens.db"
    _setup_db(str(db_path))

    now = datetime.now(timezone.utc)
    past = now - timedelta(days=1)
    future = now + timedelta(days=1)

    conn = sqlite3.connect(db_path)
    # access tokens
    conn.execute(
        "INSERT INTO access_tokens (jti, user_id, expires_at, revoked_at) VALUES (?,?,?,?)",
        ("expired", 1, _iso(past), None),
    )
    conn.execute(
        "INSERT INTO access_tokens (jti, user_id, expires_at, revoked_at) VALUES (?,?,?,?)",
        ("revoked", 1, _iso(future), _iso(past)),
    )
    conn.execute(
        "INSERT INTO access_tokens (jti, user_id, expires_at, revoked_at) VALUES (?,?,?,?)",
        ("active", 1, _iso(future), None),
    )
    # refresh tokens
    conn.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, issued_at, expires_at, revoked_at) VALUES (?,?,?,?,?)",
        (1, "h1", _iso(past), _iso(past), None),
    )
    conn.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, issued_at, expires_at, revoked_at) VALUES (?,?,?,?,?)",
        (1, "h2", _iso(past), _iso(future), _iso(past)),
    )
    conn.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, issued_at, expires_at, revoked_at) VALUES (?,?,?,?,?)",
        (1, "h3", _iso(now), _iso(future), None),
    )
    conn.commit()
    conn.close()

    monkeypatch.setenv("DB_PATH", str(db_path))

    deleted, detail = cleanup_tokens.run()

    assert deleted == 4
    assert "access=2" in detail and "refresh=2" in detail

    conn = sqlite3.connect(db_path)
    remaining_access = conn.execute("SELECT jti FROM access_tokens").fetchall()
    remaining_refresh = conn.execute("SELECT id FROM refresh_tokens").fetchall()
    conn.close()

    assert remaining_access == [("active",)]
    assert len(remaining_refresh) == 1
