# backend/jobs/world_pulse_jobs.py
# Computes World Pulse daily metrics/rankings and weekly cache rollups.
# Uses configurable weights for score:
#   score = streams*w_streams + sales_digital*w_digital + sales_vinyl*w_vinyl

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from services.season_service import SeasonScheduler

try:
    # Preferred: shared project connection helper
    from database import get_conn  # type: ignore
except Exception:
    # Fallback: local minimal connector for tests or standalone runs
    import sqlite3
    def get_conn():
        db_path = os.environ.get("DATABASE_URL", ":memory:")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn


ISO_DATE = "%Y-%m-%d"
ISO_TS = "%Y-%m-%dT%H:%M:%S"


def _today_str() -> str:
    return date.today().strftime(ISO_DATE)


def _monday_of(d: date) -> date:
    # Monday = 0
    return d - timedelta(days=d.weekday())


def _load_weights(conn) -> Tuple[float, float, float]:
    """Try to load weights from app_config('world_pulse_weights'), else defaults."""
    default = {"streams": 1.0, "digital": 10.0, "vinyl": 15.0}
    try:
        row = conn.execute(
            "SELECT value FROM app_config WHERE key = 'world_pulse_weights'"
        ).fetchone()
        if not row:
            return default["streams"], default["digital"], default["vinyl"]
        cfg = json.loads(row["value"])
        return (
            float(cfg.get("streams", default["streams"])),
            float(cfg.get("digital", default["digital"])),
            float(cfg.get("vinyl", default["vinyl"])),
        )
    except Exception:
        return default["streams"], default["digital"], default["vinyl"]


def _artist_name(conn, artist_id: int) -> str:
    # If you have an artists table, fetch it; otherwise fallback to generic
    try:
        row = conn.execute(
            "SELECT name FROM artists WHERE id = ?", (artist_id,)
        ).fetchone()
        if row and row["name"]:
            return row["name"]
    except Exception:
        pass
    return f"Artist {artist_id}"


def _log_job(conn, job_name: str, status: str, details: Dict):
    conn.execute(
        """\
        INSERT OR REPLACE INTO job_metadata(job_name, run_at, status, details)
        VALUES(?,?,?,?)
        """,
        (
            job_name,
            datetime.utcnow().strftime(ISO_TS),
            status,
            json.dumps(details, ensure_ascii=False),
        ),
    )


def compute_daily(
    conn,
    target_date: str,
    weights: Optional[Tuple[float, float, float]] = None,
    season: Optional[str] = None,
    multiplier: float = 1.0,
) -> List[Dict]:
    """
    Compute per-artist daily metrics for target_date from music_events.
    Expects music_events columns:
      event_time TEXT (ISO or date), artist_id INT, streams INT, sales_digital INT, sales_vinyl INT
    Writes to world_pulse_metrics (UPSERT by (date, artist_id)).
    Returns list of {'artist_id', 'streams','sales_digital','sales_vinyl','score','season'}.
    """
    if weights is None:
        weights = _load_weights(conn)
    w_streams, w_digital, w_vinyl = weights

    # Aggregate source data by artist for the day
    # Accept either date(event_time) == ? or raw date column "date"
    rows = conn.execute(
        """\
        SELECT
          artist_id,
          COALESCE(SUM(streams),0)        AS streams,
          COALESCE(SUM(sales_digital),0)  AS sales_digital,
          COALESCE(SUM(sales_vinyl),0)    AS sales_vinyl
        FROM music_events
        WHERE DATE(event_time) = DATE(?)
        GROUP BY artist_id
        """,
        (target_date,),
    ).fetchall()

    results = []
    for r in rows:
        streams = int(r["streams"])
        sd = int(r["sales_digital"])
        sv = int(r["sales_vinyl"])
        score = streams * w_streams + sd * w_digital + sv * w_vinyl
        score *= multiplier
        conn.execute(
            """\
            INSERT INTO world_pulse_metrics(date, artist_id, streams, sales_digital, sales_vinyl, score, season)
            VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(date, artist_id) DO UPDATE SET
              streams=excluded.streams,
              sales_digital=excluded.sales_digital,
              sales_vinyl=excluded.sales_vinyl,
              score=excluded.score,
              season=excluded.season
            """,
            (target_date, r["artist_id"], streams, sd, sv, float(score), season),
        )
        results.append(
            {
                "artist_id": r["artist_id"],
                "streams": streams,
                "sales_digital": sd,
                "sales_vinyl": sv,
                "score": float(score),
                "season": season,
            }
        )

    return results


def _pct_change(curr: Optional[float], prev: Optional[float]) -> Optional[float]:
    if curr is None or prev is None or prev == 0:
        return None
    return (curr - prev) / prev


def write_daily_rankings(conn, target_date: str, season: Optional[str] = None):
    """
    Build rankings for target_date and season from world_pulse_metrics.
    pct_change is vs previous day score for the same artist.
    """
    prev_date = (
        datetime.strptime(target_date, ISO_DATE).date() - timedelta(days=1)
    ).strftime(ISO_DATE)

    # Read today's scores
    if season is None:
        today = conn.execute(
            """\
            SELECT m.artist_id, m.score
            FROM world_pulse_metrics m
            WHERE m.date = ? AND m.season IS NULL
            ORDER BY m.score DESC, m.artist_id ASC
            """,
            (target_date,),
        ).fetchall()
        prev = conn.execute(
            "SELECT artist_id, score FROM world_pulse_metrics WHERE date = ? AND season IS NULL",
            (prev_date,),
        ).fetchall()
    else:
        today = conn.execute(
            """\
            SELECT m.artist_id, m.score
            FROM world_pulse_metrics m
            WHERE m.date = ? AND m.season = ?
            ORDER BY m.score DESC, m.artist_id ASC
            """,
            (target_date, season),
        ).fetchall()
        prev = conn.execute(
            "SELECT artist_id, score FROM world_pulse_metrics WHERE date = ? AND season = ?",
            (prev_date, season),
        ).fetchall()
    prev_map = {p["artist_id"]: float(p["score"]) for p in prev}

    # Clear existing rankings for idempotency
    if season is None:
        conn.execute(
            "DELETE FROM world_pulse_rankings WHERE date = ? AND season IS NULL",
            (target_date,),
        )
    else:
        conn.execute(
            "DELETE FROM world_pulse_rankings WHERE date = ? AND season = ?",
            (target_date, season),
        )

    # Write ranked list
    for idx, r in enumerate(today, start=1):
        artist_id = r["artist_id"]
        score = float(r["score"])
        prev_score = prev_map.get(artist_id)
        pct = _pct_change(score, prev_score)
        conn.execute(
            """\
            INSERT INTO world_pulse_rankings(date, season, rank, artist_id, name, pct_change, score)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                target_date,
                season,
                idx,
                artist_id,
                _artist_name(conn, artist_id),
                pct,
                score,
            ),
        )


def run_daily(
    target_date: Optional[str] = None,
    weights: Optional[Tuple[float, float, float]] = None,
    conn_override=None,
):
    """
    Daily: compute metrics and rankings for target_date.
    Applies seasonal score multipliers when configured.
    Writes job_metadata on success/failure.
    """
    conn = conn_override or get_conn()
    scheduler = SeasonScheduler(conn)
    try:
        if target_date is None:
            target_date = _today_str()
        season, mult = scheduler.active_season(target_date)
        with conn:
            data = compute_daily(conn, target_date, weights, season, mult)
            write_daily_rankings(conn, target_date, season)
            _log_job(
                conn,
                job_name="world_pulse_daily",
                status="ok",
                details={
                    "date": target_date,
                    "artists": len(data),
                    "season": season,
                },
            )
    except Exception as e:
        with conn:
            _log_job(
                conn,
                job_name="world_pulse_daily",
                status="error",
                details={"date": target_date, "error": str(e)},
            )
        raise


def compute_weekly_rollup(conn, week_start: str) -> List[Dict]:
    """Roll up daily metrics into week-long totals ending on ``week_start``."""
    start = datetime.strptime(week_start, ISO_DATE).date() - timedelta(days=1)
    end = start + timedelta(days=6)
    rows = conn.execute(
        """
        SELECT artist_id, COALESCE(SUM(score),0) AS score
        FROM world_pulse_metrics
        WHERE date BETWEEN DATE(?) AND DATE(?)
        GROUP BY artist_id
        ORDER BY score DESC, artist_id ASC
        """,
        (start.strftime(ISO_DATE), end.strftime(ISO_DATE)),
    ).fetchall()
    return [{"artist_id": r["artist_id"], "score": float(r["score"])} for r in rows]


def write_weekly_cache(conn, week_start: str):
    """
    Build weekly cache rankings for week_start (Monday).
    pct_change is vs previous week's total score for same artist.
    """
    ws = datetime.strptime(week_start, ISO_DATE).date()
    prev_ws = (ws - timedelta(days=7)).strftime(ISO_DATE)

    current = compute_weekly_rollup(conn, week_start)
    prev = compute_weekly_rollup(conn, prev_ws)  # previous week
    prev_map = {p["artist_id"]: p["score"] for p in prev}

    # Clear this week's cache for idempotency
    conn.execute("DELETE FROM world_pulse_weekly_cache WHERE week_start = ?", (week_start,))

    for idx, r in enumerate(current, start=1):
        artist_id = r["artist_id"]
        score = r["score"]
        pct = _pct_change(score, prev_map.get(artist_id))
        conn.execute(
            """\
            INSERT INTO world_pulse_weekly_cache(week_start, rank, artist_id, name, pct_change, score)
            VALUES(?,?,?,?,?,?)
            """,
            (week_start, idx, artist_id, _artist_name(conn, artist_id), pct, score),
        )


def run_weekly(
    week_start: Optional[str] = None,
    conn_override=None,
):
    """
    Weekly: roll up daily → weekly cache and record job stats.
    If week_start is None, computes the Monday of 'today'.
    """
    conn = conn_override or get_conn()
    try:
        if week_start is None:
            week_start = _monday_of(date.today()).strftime(ISO_DATE)
        with conn:
            write_weekly_cache(conn, week_start)
            _log_job(
                conn,
                job_name="world_pulse_weekly",
                status="ok",
                details={"week_start": week_start},
            )
    except Exception as e:
        with conn:
            _log_job(
                conn,
                job_name="world_pulse_weekly",
                status="error",
                details={"week_start": week_start, "error": str(e)},
            )
        raise


def reset_band_recordings(conn):
    """Reset the per-band recorded show counter."""
    conn.execute("UPDATE bands SET recorded_shows_year = 0")


def run_yearly(today: Optional[str] = None, conn_override=None):
    """Yearly job: reset recording counters on January 1."""
    conn = conn_override or get_conn()
    try:
        if today is None:
            today = _today_str()
        dt = datetime.strptime(today, ISO_DATE).date()
        if dt.month == 1 and dt.day == 1:
            with conn:
                reset_band_recordings(conn)
                _log_job(
                    conn,
                    job_name="world_pulse_yearly",
                    status="ok",
                    details={"date": today},
                )
    except Exception as e:
        with conn:
            _log_job(
                conn,
                job_name="world_pulse_yearly",
                status="error",
                details={"date": today, "error": str(e)},
            )
        raise


if __name__ == "__main__":
    # Handy CLI: python -m jobs.world_pulse_jobs daily 2025-08-25
    import sys
    cmd = sys.argv[1] if len(sys.argv) >= 2 else "daily"
    arg = sys.argv[2] if len(sys.argv) >= 3 else None
    if cmd == "daily":
        run_daily(target_date=arg)
    elif cmd == "weekly":
        run_weekly(week_start=arg)
    elif cmd == "yearly":
        run_yearly(today=arg)
    else:
        print("Usage: daily [YYYY-MM-DD] | weekly [YYYY-MM-DD(Mon)] | yearly [YYYY-MM-DD]")
