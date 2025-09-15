# backend/tests/test_data_hygiene_jobs.py
# Tests for data hygiene cleanup behavior
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from jobs.data_hygiene_jobs import backup_sqlite_with_rotation, cleanup_expired_records


def _mk_db(tmp_path: Path) -> str:
    db = tmp_path / "test.db"
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA foreign_keys=ON;")
    with conn:
        # Minimal idempotency table
        conn.execute(
            """
            CREATE TABLE idempotency_records (
                key TEXT PRIMARY KEY,
                value TEXT,
                expires_at TEXT
            );
            """
        )
        # Minimal rate limit table (with expires_at for clarity)
        conn.execute(
            """
            CREATE TABLE rate_limit_counters (
                bucket TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0,
                expires_at TEXT
            );
            """
        )
    conn.close()
    return str(db)


def _iso(dt):
    # store ISO8601 with Z
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@pytest.fixture()
def seeded_db(tmp_path: Path):
    db_path = _mk_db(tmp_path)
    now = datetime.now(timezone.utc)

    conn = sqlite3.connect(db_path)
    with conn:
        # Idempotency: 2 expired, 1 fresh
        conn.execute(
            "INSERT INTO idempotency_records(key, value, expires_at) VALUES (?, ?, ?);",
            ("idem_old_1", "x", _iso(now - timedelta(days=2))),
        )
        conn.execute(
            "INSERT INTO idempotency_records(key, value, expires_at) VALUES (?, ?, ?);",
            ("idem_old_2", "y", _iso(now - timedelta(hours=1))),
        )
        conn.execute(
            "INSERT INTO idempotency_records(key, value, expires_at) VALUES (?, ?, ?);",
            ("idem_fresh", "z", _iso(now + timedelta(days=1))),
        )

        # Rate limit: 1 expired, 2 fresh
        conn.execute(
            "INSERT INTO rate_limit_counters(bucket, count, expires_at) VALUES (?, ?, ?);",
            ("rl_old", 5, _iso(now - timedelta(seconds=10))),
        )
        conn.execute(
            "INSERT INTO rate_limit_counters(bucket, count, expires_at) VALUES (?, ?, ?);",
            ("rl_fresh_1", 3, _iso(now + timedelta(hours=3))),
        )
        conn.execute(
            "INSERT INTO rate_limit_counters(bucket, count, expires_at) VALUES (?, ?, ?);",
            ("rl_fresh_2", 0, _iso(now + timedelta(days=2))),
        )
    conn.close()
    return db_path


def _count(conn: sqlite3.Connection, table: str) -> int:
    cur = conn.execute(f"SELECT COUNT(*) FROM {table};")
    return int(cur.fetchone()[0])


def test_cleanup_deletes_only_expired(seeded_db: str):
    # Dry-run first
    stats = cleanup_expired_records(db_path=seeded_db, dry_run=True)
    assert stats["db_path"].endswith("test.db")
    assert stats["dry_run"] is True

    # Real delete
    stats = cleanup_expired_records(db_path=seeded_db, dry_run=False)
    assert stats["dry_run"] is False
    # Expect 2 expired idempotency + 1 expired rate-limit deleted
    assert stats["idempotency_deleted"] == 2
    assert stats["rate_limit_deleted"] == 1

    # Verify DB state
    conn = sqlite3.connect(seeded_db)
    with conn:
        assert _count(conn, "idempotency_records") == 1  # only fresh remains
        assert _count(conn, "rate_limit_counters") == 2  # two fresh remain
    conn.close()


def test_backup_and_rotation(tmp_path: Path):
    # create a tiny db
    db_path = _mk_db(tmp_path)

    # First backup
    out1 = backup_sqlite_with_rotation(db_path=db_path, backup_dir=str(tmp_path / "bk"), prefix="snap", copies=2)
    assert out1.exists()

    # Second backup
    out2 = backup_sqlite_with_rotation(db_path=db_path, backup_dir=str(tmp_path / "bk"), prefix="snap", copies=2)
    assert out2.exists()

    # Third backup triggers rotation (keep=2)
    out3 = backup_sqlite_with_rotation(db_path=db_path, backup_dir=str(tmp_path / "bk"), prefix="snap", copies=2)
    assert out3.exists()

    # Ensure only 2 backups remain
    files = sorted((tmp_path / "bk").glob("snap_*.db"))
    assert len(files) == 2
