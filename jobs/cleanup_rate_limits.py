# cleanup_rate_limits.py
"""
Purge stale rate limit counters.

Environment/config:
- RATE_LIMIT_TTL_DAYS (int) optional; if present, delete rows older than TTL
- Table expected: rate_limit_counters (key TEXT, window_start TEXT, window_end TEXT, last_update TEXT)
"""

from __future__ import annotations
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Tuple

# Prefer project's shared DB util if present
try:
    from core.db import get_conn  # type: ignore
except Exception:
    def get_conn() -> sqlite3.Connection:
        db_path = os.getenv("DB_PATH", "app.db")
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run() -> Tuple[int, str]:
    """
    Returns: (rows_deleted, detail)
    """
    ttl_days_env = os.getenv("RATE_LIMIT_TTL_DAYS")
    ttl_days = int(ttl_days_env) if ttl_days_env else None

    with get_conn() as conn:
        cur = conn.cursor()
        deleted_by_window = 0
        deleted_by_ttl = 0

        # Remove counters whose window has already ended
        try:
            cur.execute("""
                DELETE FROM rate_limit_counters
                WHERE COALESCE(window_end, '') <> ''
                  AND datetime(window_end) <= datetime(?)
            """, (_now_utc_iso(),))
            deleted_by_window = cur.rowcount if cur.rowcount is not None else 0
        except sqlite3.OperationalError:
            deleted_by_window = 0

        # Remove anything older than TTL by last_update (or window_end fallback)
        if ttl_days is not None and ttl_days >= 0:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=ttl_days)).replace(microsecond=0).isoformat()
            try:
                cur.execute("""
                    DELETE FROM rate_limit_counters
                    WHERE 
                      (COALESCE(last_update,'') <> '' AND datetime(last_update) <= datetime(?))
                      OR
                      (COALESCE(last_update,'') = '' AND COALESCE(window_end,'') <> '' AND datetime(window_end) <= datetime(?))
                """, (cutoff, cutoff))
                deleted_by_ttl = cur.rowcount if cur.rowcount is not None else 0
            except sqlite3.OperationalError:
                deleted_by_ttl = 0

        conn.commit()

    total = deleted_by_window + deleted_by_ttl
    detail = f"ended_windows={deleted_by_window}, ttl={deleted_by_ttl}"
    return total, detail
