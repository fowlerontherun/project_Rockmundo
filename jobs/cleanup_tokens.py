# cleanup_tokens.py
"""
Remove expired or revoked token entries from backend.auth tables.

Targets tables:
- access_tokens(jti TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
  expires_at TEXT NOT NULL, revoked_at TEXT)
- refresh_tokens(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
  token_hash TEXT, issued_at TEXT, expires_at TEXT, revoked_at TEXT,
  user_agent TEXT, ip TEXT)

This job removes rows whose `expires_at` has passed or whose
`revoked_at` timestamp is in the past.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from typing import Tuple

# Prefer project's shared DB util if present
try:  # pragma: no cover - optional import
    from core.db import get_conn  # type: ignore
except Exception:  # pragma: no cover - fallback for tests/standalone
    def get_conn() -> sqlite3.Connection:
        db_path = os.getenv("DB_PATH", "app.db")
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _cleanup_table(cur: sqlite3.Cursor, table: str, now_iso: str) -> int:
    cur.execute(
        f"""
        DELETE FROM {table}
        WHERE datetime(expires_at) <= datetime(?)
           OR (COALESCE(revoked_at, '') <> '' AND datetime(revoked_at) <= datetime(?))
        """,
        (now_iso, now_iso),
    )
    return cur.rowcount if cur.rowcount is not None else 0


def run() -> Tuple[int, str]:
    """Execute cleanup and return (rows_deleted, detail)."""
    now_iso = _now_utc_iso()
    with get_conn() as conn:
        cur = conn.cursor()
        deleted_access = 0
        deleted_refresh = 0

        try:
            deleted_access = _cleanup_table(cur, "access_tokens", now_iso)
        except sqlite3.OperationalError:
            deleted_access = 0

        try:
            deleted_refresh = _cleanup_table(cur, "refresh_tokens", now_iso)
        except sqlite3.OperationalError:
            deleted_refresh = 0

        conn.commit()

    total = deleted_access + deleted_refresh
    detail = f"access={deleted_access}, refresh={deleted_refresh}"
    return total, detail
