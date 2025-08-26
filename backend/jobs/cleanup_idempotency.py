# cleanup_idempotency.py
"""
Purge expired idempotency records to keep the DB lean.

Environment/config:
- IDEMPOTENCY_TTL_DAYS (int) optional; if present, purge any rows older than TTL
- Table expected: idempotency_records(key TEXT PK, created_at TEXT ISO8601, expires_at TEXT ISO8601)
"""

from __future__ import annotations
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Tuple

# Prefer project's shared DB util if present
try:
    from backend.core.db import get_conn  # type: ignore
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
    ttl_days_env = os.getenv("IDEMPOTENCY_TTL_DAYS")
    ttl_days = int(ttl_days_env) if ttl_days_env else None

    with get_conn() as conn:
        cur = conn.cursor()

        # Purge any past-expiry rows, if column exists
        # Be tolerant if schema differs; no-op if table missing.
        try:
            # 1) rows with expires_at in the past
            cur.execute("""
                DELETE FROM idempotency_records
                WHERE COALESCE(expires_at, '') <> ''
                  AND datetime(expires_at) <= datetime(?)
            """, (_now_utc_iso(),))
            deleted_by_expiry = cur.rowcount if cur.rowcount is not None else 0
        except sqlite3.OperationalError:
            # table or column not found: no-op
            deleted_by_expiry = 0

        deleted_by_ttl = 0
        if ttl_days is not None and ttl_days >= 0:
            try:
                cutoff = (datetime.now(timezone.utc) - timedelta(days=ttl_days)).replace(microsecond=0).isoformat()
                cur.execute("""
                    DELETE FROM idempotency_records
                    WHERE datetime(created_at) <= datetime(?)
                """, (cutoff,))
                deleted_by_ttl = cur.rowcount if cur.rowcount is not None else 0
            except sqlite3.OperationalError:
                deleted_by_ttl = 0

        conn.commit()

    total = deleted_by_expiry + deleted_by_ttl
    detail = f"expired={deleted_by_expiry}, ttl={deleted_by_ttl}"
    return total, detail
