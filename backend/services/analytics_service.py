# File: backend/services/analytics_service.py
"""
Admin Analytics Service
-----------------------
Read-only KPIs and leaderboards for streams, digital sales, vinyl, tickets,
and royalties. Queries are resilient: if a table doesn't exist yet, that
section is simply skipped so the API still returns useful data.
"""

import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.seeds.skill_seed import SEED_SKILLS
from backend.services.skill_service import skill_service

from utils.db import get_conn

from backend import database
from backend.models.analytics import AggregatedMetrics, MetricPoint
from backend.utils.metrics import _REGISTRY, Histogram

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


if "service_latency_ms" in _REGISTRY:
    SERVICE_LATENCY_MS = _REGISTRY["service_latency_ms"]  # type: ignore[assignment]
else:
    SERVICE_LATENCY_MS = Histogram(
        "service_latency_ms",
        "Service call latency in milliseconds",
        [50, 100, 250, 500, 1000, 2500, 5000],
        ("service", "operation"),
    )

DATA_ANALYTICS_SKILL = next(s for s in SEED_SKILLS if s.name == "data_analytics")

class AnalyticsService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)

    # ---------- helpers ----------
    def _table_exists(self, cur, name: str) -> bool:
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None

    def _fetchall(self, cur) -> List[Dict[str, Any]]:
        return [dict(r) for r in cur.fetchall()]

    # ---------- KPIs ----------
    def kpis(self, period_start: str, period_end: str) -> Dict[str, Any]:
        """
        High-level aggregates between [period_start, period_end] inclusive (UTC).
        """
        start = time.perf_counter()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()

                res = {
                    "streams": {"plays": 0},
                    "radio": {"plays": 0},
                    "digital": {"revenue_cents": 0, "count": 0},
                    "vinyl": {"revenue_cents": 0, "units": 0},
                    "tickets": {"revenue_cents": 0, "orders": 0},
                }

                # Streams
                if self._table_exists(cur, "streams"):
                    cur.execute("""
                        SELECT COUNT(*)
                        FROM streams
                        WHERE datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?)
                    """, (f"{period_start} 00:00:00", f"{period_end} 23:59:59"))
                    res["streams"]["plays"] = int(cur.fetchone()[0])

                # Radio listeners
                if self._table_exists(cur, "radio_listeners"):
                    cur.execute(
                        """
                        SELECT COUNT(*)
                        FROM radio_listeners
                        WHERE datetime(listened_at) >= datetime(?) AND datetime(listened_at) <= datetime(?)
                        """,
                        (f"{period_start} 00:00:00", f"{period_end} 23:59:59"),
                    )
                    res["radio"]["plays"] = int(cur.fetchone()[0])

                # Digital sales
                if self._table_exists(cur, "digital_sales"):
                    cur.execute("""
                        SELECT IFNULL(SUM(price_cents),0), COUNT(*)
                        FROM digital_sales
                        WHERE datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?)
                    """, (f"{period_start} 00:00:00", f"{period_end} 23:59:59"))
                    cents, cnt = cur.fetchone()
                    res["digital"]["revenue_cents"] = int(cents or 0)
                    res["digital"]["count"] = int(cnt or 0)

                # Vinyl
                if all(self._table_exists(cur, t) for t in ("vinyl_order_items","vinyl_orders")):
                    cur.execute("""
                        SELECT IFNULL(SUM(oi.unit_price_cents * (oi.qty - oi.refunded_qty)),0) AS rev,
                               IFNULL(SUM(oi.qty - oi.refunded_qty),0) AS units
                        FROM vinyl_order_items oi
                        JOIN vinyl_orders o ON o.id = oi.order_id
                        WHERE o.status = 'confirmed'
                          AND datetime(o.created_at) >= datetime(?)
                          AND datetime(o.created_at) <= datetime(?)
                    """, (f"{period_start} 00:00:00", f"{period_end} 23:59:59"))
                    rev, units = cur.fetchone()
                    res["vinyl"]["revenue_cents"] = int(rev or 0)
                    res["vinyl"]["units"] = int(units or 0)

                # Tickets
                if self._table_exists(cur, "ticket_orders"):
                    cur.execute("""
                        SELECT IFNULL(SUM(total_cents),0), COUNT(*)
                        FROM ticket_orders
                        WHERE status = 'confirmed'
                          AND datetime(created_at) >= datetime(?)
                          AND datetime(created_at) <= datetime(?)
                    """, (f"{period_start} 00:00:00", f"{period_end} 23:59:59"))
                    rev, cnt = cur.fetchone()
                    res["tickets"]["revenue_cents"] = int(rev or 0)
                    res["tickets"]["orders"] = int(cnt or 0)

                return res
        finally:
            SERVICE_LATENCY_MS.labels("analytics_service", "kpis").observe(
                (time.perf_counter() - start) * 1000
            )

    # ---------- Leaderboards ----------
    def top_songs(self, period_start: str, period_end: str, limit: int = 20) -> Dict[str, Any]:
        """
        Return two lists:
        - streams: top songs by play count
        - digital: top songs by digital revenue (cents)
        Adds 'title' if a songs table exists.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # Streams
            streams = []
            if self._table_exists(cur, "streams"):
                cur.execute("""
                    SELECT s.song_id, COUNT(*) AS plays
                    FROM streams s
                    WHERE datetime(s.created_at) >= datetime(?)
                      AND datetime(s.created_at) <= datetime(?)
                    GROUP BY s.song_id
                    ORDER BY plays DESC, s.song_id ASC
                    LIMIT ?
                """, (f"{period_start} 00:00:00", f"{period_end} 23:59:59", limit))
                streams = self._fetchall(cur)

            # Digital
            digital = []
            if self._table_exists(cur, "digital_sales"):
                cur.execute("""
                    SELECT work_id AS song_id, SUM(price_cents) AS revenue_cents, COUNT(*) AS purchases
                    FROM digital_sales
                    WHERE work_type = 'song'
                      AND datetime(created_at) >= datetime(?)
                      AND datetime(created_at) <= datetime(?)
                    GROUP BY work_id
                    ORDER BY revenue_cents DESC, work_id ASC
                    LIMIT ?
                """, (f"{period_start} 00:00:00", f"{period_end} 23:59:59", limit))
                digital = self._fetchall(cur)

            # Titles, if available
            titles = {}
            try:
                cur.execute("SELECT id, title FROM songs")
                titles = {int(r["id"]): r["title"] for r in cur.fetchall()}
            except Exception:
                pass

            for r in streams:
                r["title"] = titles.get(int(r["song_id"]))
            for r in digital:
                r["title"] = titles.get(int(r["song_id"]))

            return {"streams": streams, "digital": digital}

    def top_albums(self, period_start: str, period_end: str, limit: int = 20) -> Dict[str, Any]:
        """
        Return two lists:
        - digital: top albums by digital revenue (cents)
        - vinyl: top albums by vinyl revenue (cents) and units
        Adds 'title' if an albums table exists.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            digital = []
            if self._table_exists(cur, "digital_sales"):
                cur.execute("""
                    SELECT work_id AS album_id, SUM(price_cents) AS revenue_cents, COUNT(*) AS purchases
                    FROM digital_sales
                    WHERE work_type = 'album'
                      AND datetime(created_at) >= datetime(?)
                      AND datetime(created_at) <= datetime(?)
                    GROUP BY work_id
                    ORDER BY revenue_cents DESC, work_id ASC
                    LIMIT ?
                """, (f"{period_start} 00:00:00", f"{period_end} 23:59:59", limit))
                digital = self._fetchall(cur)

            vinyl = []
            if all(self._table_exists(cur, t) for t in ("vinyl_order_items","vinyl_orders","vinyl_skus" )):
                cur.execute("""
                    SELECT s.album_id, SUM(oi.unit_price_cents * (oi.qty - oi.refunded_qty)) AS revenue_cents,
                           SUM(oi.qty - oi.refunded_qty) AS units
                    FROM vinyl_order_items oi
                    JOIN vinyl_orders o ON o.id = oi.order_id
                    JOIN vinyl_skus s ON s.id = oi.sku_id
                    WHERE o.status = 'confirmed'
                      AND datetime(o.created_at) >= datetime(?)
                      AND datetime(o.created_at) <= datetime(?)
                    GROUP BY s.album_id
                    ORDER BY revenue_cents DESC, s.album_id ASC
                    LIMIT ?
                """, (f"{period_start} 00:00:00", f"{period_end} 23:59:59", limit))
                vinyl = self._fetchall(cur)

            # Titles, if available
            titles = {}
            try:
                cur.execute("SELECT id, title FROM albums")
                titles = {int(r["id"]): r["title"] for r in cur.fetchall()}
            except Exception:
                pass

            for r in digital:
                r["title"] = titles.get(int(r["album_id"])) 
            for r in vinyl:
                r["title"] = titles.get(int(r["album_id"]))

            return {"digital": digital, "vinyl": vinyl}

    def genre_breakdown(self) -> List[Dict[str, int]]:
        """Aggregate song counts by genre and subgenre IDs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            if not self._table_exists(cur, "songs"):
                return []

            cur.execute(
                """
                SELECT COALESCE(g.parent_id, s.genre_id) AS genre_id,
                       s.genre_id AS subgenre_id,
                       COUNT(*) AS count
                FROM songs s
                LEFT JOIN genres g ON g.id = s.genre_id
                GROUP BY genre_id, subgenre_id
                ORDER BY count DESC
                """
            )
            return self._fetchall(cur)

    # ---------- Royalty views ----------
    def recent_royalty_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if not self._table_exists(cur, "royalty_runs"):
                return []
            cur.execute("""
                SELECT * FROM royalty_runs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            return self._fetchall(cur)

    # ---------- aggregated metrics ----------
    def time_series(self, start_date: str, end_date: str) -> AggregatedMetrics:
        """Return time-series metrics for economy, events, and skills.

        The results are cached per (db_path, start_date, end_date) triple to
        avoid recalculating heavy queries repeatedly.
        """

        db = self.db_path
        economy = _economy_series(db, start_date, end_date)
        events = _event_series(db, start_date, end_date)
        skills = _skill_series(db, start_date, end_date)
        return AggregatedMetrics(economy=economy, events=events, skills=skills)

    def royalties_summary_by_band(self, run_id: int) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if not self._table_exists(cur, "royalty_run_lines"):
                return []
            cur.execute("""
                SELECT band_id, SUM(amount_cents) AS amount_cents
                FROM royalty_run_lines
                WHERE run_id = ?
                GROUP BY band_id
                ORDER BY amount_cents DESC
            """, (run_id,))
            return self._fetchall(cur)

    def sales_forecast(self, user_id: int, history: List[int]) -> Dict[str, Any]:
        """Forecast upcoming sales using the user's analytics skill.

        Viewing the forecast trains the ``data_analytics`` skill. Higher skill
        levels yield more accurate predictions and unlock confidence metrics.
        """

        skill = skill_service.train(user_id, DATA_ANALYTICS_SKILL, 100)
        avg = sum(history) / len(history)
        if skill.level >= 5:
            margin = 0.05
        elif skill.level >= 3:
            margin = 0.15
        else:
            margin = 0.30
        forecast = int(avg * (1 + margin))
        res: Dict[str, Any] = {"forecast": forecast, "skill_level": skill.level}
        if skill.level >= 5:
            res["confidence"] = 1 - margin
        return res


def _daterange(start: str, end: str) -> List[str]:
    s = datetime.fromisoformat(start).date()
    e = datetime.fromisoformat(end).date()
    days = (e - s).days
    return [(s + timedelta(days=i)).isoformat() for i in range(days + 1)]


def _build_series(rows: Dict[str, int], start: str, end: str) -> List[MetricPoint]:
    return [MetricPoint(date=d, value=rows.get(d, 0)) for d in _daterange(start, end)]


@lru_cache(maxsize=128)
def _economy_series(db_path: str, start: str, end: str) -> List[MetricPoint]:
    with get_conn(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT date(created_at) AS d, SUM(amount_cents) AS v
            FROM transactions
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY d
            """,
            (start, end),
        )
        rows = {r["d"]: int(r["v"] or 0) for r in cur.fetchall()}
    return _build_series(rows, start, end)


@lru_cache(maxsize=128)
def _event_series(db_path: str, start: str, end: str) -> List[MetricPoint]:
    with get_conn(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT date(start_date) AS d, COUNT(*) AS c
            FROM active_events
            WHERE date(start_date) BETWEEN ? AND ?
            GROUP BY d
            """,
            (start, end),
        )
        rows = {r["d"]: int(r["c"] or 0) for r in cur.fetchall()}
    return _build_series(rows, start, end)


@lru_cache(maxsize=128)
def _skill_series(db_path: str, start: str, end: str) -> List[MetricPoint]:
    with get_conn(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT date(created_at) AS d, SUM(amount) AS a
            FROM skill_progress
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY d
            """,
            (start, end),
        )
        rows = {r["d"]: int(r["a"] or 0) for r in cur.fetchall()}
    return _build_series(rows, start, end)


class ScheduleAnalyticsService:
    """Aggregate scheduled hours and rest compliance."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path

    def weekly_totals(self, user_id: int, week_start: str) -> Dict[str, Any]:
        """Return per-category totals and daily rest compliance for a week."""
        db_path = self.db_path or database.DB_PATH
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ds.date, a.category, a.duration_hours
                FROM daily_schedule ds
                JOIN activities a ON ds.activity_id = a.id
                WHERE ds.user_id = ?
                  AND ds.date BETWEEN ? AND date(?, '+6 days')
                """,
                (user_id, week_start, week_start),
            )
            rows = cur.fetchall()

        totals: Dict[str, float] = defaultdict(float)
        rest_by_day: Dict[str, float] = defaultdict(float)
        for day, category, hours in rows:
            cat = category or "other"
            totals[cat] += float(hours)
            if cat in {"rest", "sleep"}:
                rest_by_day[day] += float(hours)

        start_date = datetime.fromisoformat(week_start)
        rest_stats: List[Dict[str, Any]] = []
        for i in range(7):
            d = (start_date + timedelta(days=i)).date().isoformat()
            h = rest_by_day.get(d, 0.0)
            rest_stats.append({"date": d, "rest_hours": h, "compliant": h >= 5})

        return {"totals": dict(totals), "rest": rest_stats}


schedule_analytics_service = ScheduleAnalyticsService()

__all__ = [
    "AnalyticsService",
    "ScheduleAnalyticsService",
    "schedule_analytics_service",
]
