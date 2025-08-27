from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional

from utils.db import cached_query

from backend.models.analytics import (
    AgeBucket,
    FanSegmentSummary,
    FanTrends,
    MetricPoint,
    RegionBucket,
    SpendBucket,
)


class FanInsightService:
    """Aggregate fan engagement and demographics."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or ""

    # ----- public API -----
    def segment_summary(self) -> FanSegmentSummary:
        return FanSegmentSummary(
            age=_age_buckets(self.db_path),
            region=_region_buckets(self.db_path),
            spend=_spend_buckets(self.db_path),
        )

    def trends(self, start_date: str, end_date: str) -> FanTrends:
        return FanTrends(
            events=_event_series(self.db_path, start_date, end_date),
            purchases=_purchase_series(self.db_path, start_date, end_date),
            streams=_stream_series(self.db_path, start_date, end_date),
        )


# ----- helpers -----

def _daterange(start: str, end: str):
    d = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    while d <= end_dt:
        yield d.strftime("%Y-%m-%d")
        d += timedelta(days=1)


def _build_series(rows: Dict[str, int], start: str, end: str):
    return [MetricPoint(date=d, value=rows.get(d, 0)) for d in _daterange(start, end)]


def _age_buckets(db_path: str):
    rows = cached_query(
        db_path,
        """
        SELECT CASE
                 WHEN age < 18 THEN '<18'
                 WHEN age BETWEEN 18 AND 24 THEN '18-24'
                 WHEN age BETWEEN 25 AND 34 THEN '25-34'
                 ELSE '35+'
               END AS bucket,
               COUNT(*) AS fans
        FROM users
        GROUP BY bucket
        """,
    )
    return [AgeBucket(bucket=r["bucket"], fans=int(r["fans"])) for r in rows]


def _region_buckets(db_path: str):
    rows = cached_query(
        db_path,
        "SELECT region, COUNT(*) AS fans FROM users GROUP BY region",
    )
    return [RegionBucket(region=r["region"], fans=int(r["fans"])) for r in rows]


def _spend_buckets(db_path: str):
    rows = cached_query(
        db_path,
        """
        SELECT CASE
                 WHEN total < 1000 THEN 'low'
                 WHEN total < 5000 THEN 'mid'
                 ELSE 'high'
               END AS bucket,
               COUNT(*) AS fans
        FROM (
            SELECT u.id AS user_id, IFNULL(SUM(p.amount_cents),0) AS total
            FROM users u
            LEFT JOIN purchases p ON u.id = p.user_id
            GROUP BY u.id
        )
        GROUP BY bucket
        """,
    )
    return [SpendBucket(bucket=r["bucket"], fans=int(r["fans"])) for r in rows]


def _event_series(db_path: str, start: str, end: str):
    rows = cached_query(
        db_path,
        """
        SELECT date(created_at) AS d, COUNT(*) AS c
        FROM events
        WHERE date(created_at) BETWEEN ? AND ?
        GROUP BY d
        """,
        (start, end),
    )
    row_map = {r["d"]: int(r["c"] or 0) for r in rows}
    return _build_series(row_map, start, end)


def _purchase_series(db_path: str, start: str, end: str):
    rows = cached_query(
        db_path,
        """
        SELECT date(created_at) AS d, SUM(amount_cents) AS s
        FROM purchases
        WHERE date(created_at) BETWEEN ? AND ?
        GROUP BY d
        """,
        (start, end),
    )
    row_map = {r["d"]: int(r["s"] or 0) for r in rows}
    return _build_series(row_map, start, end)


def _stream_series(db_path: str, start: str, end: str):
    rows = cached_query(
        db_path,
        """
        SELECT date(created_at) AS d, COUNT(*) AS c
        FROM streams
        WHERE date(created_at) BETWEEN ? AND ?
        GROUP BY d
        """,
        (start, end),
    )
    row_map = {r["d"]: int(r["c"] or 0) for r in rows}
    return _build_series(row_map, start, end)
