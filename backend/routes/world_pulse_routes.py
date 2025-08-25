# File: backend/routes/world_pulse_routes.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from utils.db import get_conn

router = APIRouter(prefix="/world-pulse", tags=["WorldPulse"])

@router.get("/daily")
def world_pulse_daily(top_n: int = 20) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        try:
            rows = conn.execute("""
                SELECT COALESCE(name, artist, band_name) AS name,
                       COALESCE(rank, ranking, position, 0) AS rank,
                       COALESCE(pct_change, change_pct, delta_pct, 0.0) AS pct_change
                FROM world_pulse_rankings
                ORDER BY rank ASC
                LIMIT ?
            """, (top_n,)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

@router.get("/weekly")
def world_pulse_weekly(top_n: int = 20) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        try:
            rows = conn.execute("""
                SELECT COALESCE(name, artist, band_name) AS name,
                       COALESCE(rank, ranking, position, 0) AS rank,
                       COALESCE(pct_change, change_pct, delta_pct, 0.0) AS pct_change
                FROM world_pulse_weekly_cache
                ORDER BY rank ASC
                LIMIT ?
            """, (top_n,)).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

@router.get("/health")
def world_pulse_health():
    with get_conn() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS job_metadata (
            key TEXT PRIMARY KEY, value TEXT, updated_at TEXT DEFAULT (datetime('now'))
        )""")
        daily = conn.execute("SELECT updated_at FROM job_metadata WHERE key='world_pulse_daily_last_run'").fetchone()
        weekly = conn.execute("SELECT updated_at FROM job_metadata WHERE key='world_pulse_weekly_last_run'").fetchone()
        return {
            "daily_last_run": daily["updated_at"] if daily else None,
            "weekly_last_run": weekly["updated_at"] if weekly else None,
        }
