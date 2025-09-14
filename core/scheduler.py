# scheduler.py
"""
Lightweight job scheduler + runner registry.

- Registers known jobs
- Provides programmatic triggers
- Records job_history rows
- Optional periodic scheduling via asyncio tasks (disabled by default here;
  can be enabled in your app lifespan/startup)

Expose:
- register_jobs()
- list_jobs()
- run_job(job_name: str) -> dict (result summary)
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from datetime import datetime, timezone
from typing import Callable, Dict, Optional

# Prefer project's get_conn
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

# Import job modules
from jobs import (
    backup_db,
    cleanup_event_effects,
    cleanup_idempotency,
    cleanup_rate_limits,
    cleanup_tokens,
    lifestyle_jobs,
    random_events,
)  # type: ignore

JobFunc = Callable[[], tuple[int, str]]

_registry: Dict[str, JobFunc] = {}
_last_results: Dict[str, dict] = {}


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def register_jobs() -> None:
    _registry.clear()
    _registry["cleanup_idempotency"] = cleanup_idempotency.run
    _registry["cleanup_rate_limits"] = cleanup_rate_limits.run
    _registry["cleanup_tokens"] = cleanup_tokens.run
    _registry["backup_db"] = backup_db.run
    _registry["cleanup_event_effects"] = cleanup_event_effects.run
    _registry["random_events"] = random_events.run
    _registry["lifestyle_jobs"] = lifestyle_jobs.run


def list_jobs() -> dict:
    return {
        "registered": sorted(list(_registry.keys())),
        "last_results": _last_results,
    }


def _insert_history_start(job_name: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO job_history (job_name, started_at, status)
            VALUES (?, ?, 'running')
            """,
            (job_name, _utc_iso()),
        )
        return int(cur.lastrowid)


def _update_history_finish(row_id: int, status: str, duration_ms: int, rows_affected: int, detail: str, error: Optional[str]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE job_history
               SET finished_at = ?, status = ?, duration_ms = ?, rows_affected = ?, detail = ?, error = ?
             WHERE id = ?
            """,
            (_utc_iso(), status, duration_ms, rows_affected, detail, error, row_id),
        )


async def run_job(job_name: str) -> dict:
    if job_name not in _registry:
        return {"ok": False, "error": f"unknown job '{job_name}'"}

    job = _registry[job_name]
    hist_id = _insert_history_start(job_name)

    started = datetime.now(timezone.utc)
    error_msg = None
    status = "success"
    rows = 0
    detail = ""

    try:
        # Run in a thread, so sync jobs don't block event loop
        rows, detail = await asyncio.to_thread(job)
    except Exception as e:
        status = "error"
        error_msg = f"{type(e).__name__}: {e}"

    finished = datetime.now(timezone.utc)
    duration_ms = int((finished - started).total_seconds() * 1000)

    _update_history_finish(hist_id, status, duration_ms, rows, detail, error_msg)

    result = {
        "ok": status == "success",
        "job": job_name,
        "rows_affected": rows,
        "detail": detail,
        "status": status,
        "duration_ms": duration_ms,
        "history_id": hist_id,
        "error": error_msg,
    }
    _last_results[job_name] = result
    return result
