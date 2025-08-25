# File: backend/jobs/world_pulse_jobs.py
from __future__ import annotations
from typing import Optional
from utils.db import get_conn

DDL = """
CREATE TABLE IF NOT EXISTS job_metadata (
  key TEXT PRIMARY KEY,
  value TEXT,
  updated_at TEXT DEFAULT (datetime('now'))
);
"""

def _set_meta(conn, key: str, value: str):
    conn.execute("""INSERT INTO job_metadata(key, value, updated_at)
                    VALUES(?, ?, datetime('now'))
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')""",
                 (key, value))

async def run_daily_world_pulse(db_path: Optional[str] = None) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(DDL)
        _set_meta(conn, "world_pulse_daily_last_run", "ok")

async def run_weekly_rollup(db_path: Optional[str] = None) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(DDL)
        _set_meta(conn, "world_pulse_weekly_last_run", "ok")
