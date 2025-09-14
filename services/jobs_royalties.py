# File: backend/services/jobs_royalties.py
"""
Royalty Jobs Service
Aggregates revenue from streams + digital sales + vinyl into royalty_run_lines.
- Streams: sums per-song plays (anti-fraud cap per user/song/day) * per-stream rate
- Digital: sums digital_sales per work (song/album)
- Vinyl: sums per album via vinyl_order_items -> vinyl_skus(album_id)

If collaborations are present (table 'collaborations' with columns:
  work_type, work_id, band_a_id, band_b_id, split_a_pct, split_b_pct),
the amounts are split accordingly. Otherwise, full amount goes to the owner band
(if discoverable via songs.band_id or albums.band_id).

All tables are optional; if missing, that channel is skipped gracefully.
"""

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.utils.metrics import Counter
from config.revenue import (
    DAILY_STREAM_CAP_PER_USER_PER_SONG,
    SPONSOR_IMPRESSION_RATE_CENTS,
    SPONSOR_PAYOUT_SPLIT,
    STREAM_RATE_MICROCENTS,
)

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

ROYALTY_JOB_FAILURES = Counter(
    "royalty_job_failures_total", "Total failed royalty job runs", labelnames=("region",)
)
ROYALTY_JOB_SUCCESS = Counter(
    "royalty_job_success_total", "Total successful royalty job runs", labelnames=("region",)
)

class RoyaltyJobError(Exception):
    pass

@dataclass
class RunWindow:
    start: str  # 'YYYY-MM-DD'
    end: str    # 'YYYY-MM-DD' (inclusive end handled in SQL <= end 23:59:59)

class RoyaltyJobsService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)

    # -------- core helpers --------
    def _table_exists(self, cur, name: str) -> bool:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS royalty_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              period_start TEXT NOT NULL,
              period_end TEXT NOT NULL,
              region TEXT NOT NULL DEFAULT 'global',
              status TEXT NOT NULL DEFAULT 'pending',
              notes TEXT,
              created_at TEXT DEFAULT (datetime('now')),
              updated_at TEXT
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS royalty_run_lines (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id INTEGER NOT NULL,
              region TEXT NOT NULL DEFAULT 'global',
              work_type TEXT NOT NULL,
              work_id INTEGER,
              band_id INTEGER,
              collaborator_band_id INTEGER,
              source TEXT NOT NULL,
              amount_cents INTEGER NOT NULL,
              meta_json TEXT,
              created_at TEXT DEFAULT (datetime('now'))
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS ix_royalty_lines_run ON royalty_run_lines(run_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_royalty_lines_band ON royalty_run_lines(band_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_royalty_lines_work ON royalty_run_lines(work_type, work_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_royalty_runs_region ON royalty_runs(region)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_royalty_lines_region ON royalty_run_lines(region)")
            # Backfill region column if upgrading from older schema
            for table in ("royalty_runs", "royalty_run_lines"):
                cur.execute(f"PRAGMA table_info({table})")
                cols = {row[1] for row in cur.fetchall()}
                if "region" not in cols:
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN region TEXT DEFAULT 'global'")
            conn.commit()

    def _has_column(self, cur, table: str, column: str) -> bool:
        cur.execute(f"PRAGMA table_info({table})")
        return any(row[1].lower() == column.lower() for row in cur.fetchall())

    def _region_filter(self, cur, table: str, region: str, alias: str = "") -> Tuple[str, List[str]]:
        if region == "global":
            return "", []
        for col in ("region", "country_code", "country"):
            if self._has_column(cur, table, col):
                prefix = f"{alias}." if alias else ""
                return f" AND {prefix}{col} = ?", [region]
        return "", []

    def _create_run(self, cur, window: RunWindow, region: str) -> int:
        cur.execute(
            """
            INSERT INTO royalty_runs (period_start, period_end, region, status)
            VALUES (?, ?, ?, 'running')
        """,
            (window.start, window.end, region),
        )
        return cur.lastrowid

    def _complete_run(self, cur, run_id: int, notes: Optional[str] = None) -> None:
        cur.execute("""
            UPDATE royalty_runs SET status='completed', updated_at=datetime('now'), notes=COALESCE(notes, ?)
            WHERE id = ?
        """, (notes, run_id))

    def _fail_run(self, cur, run_id: int, err: str) -> None:
        cur.execute("""
            UPDATE royalty_runs SET status='failed', updated_at=datetime('now'), notes=?
            WHERE id = ?
        """, (err, run_id))

    # -------- ownership / collabs --------
    def _owner_band_for_work(self, cur, work_type: str, work_id: int) -> Optional[int]:
        try:
            if work_type == "song":
                cur.execute("SELECT band_id FROM songs WHERE id = ?", (work_id,))
                row = cur.fetchone()
                return int(row[0]) if row and row[0] is not None else None
            if work_type == "album":
                cur.execute("SELECT band_id FROM albums WHERE id = ?", (work_id,))
                row = cur.fetchone()
                return int(row[0]) if row and row[0] is not None else None
        except Exception:
            return None
        return None

    def _collab_split(self, cur, work_type: str, work_id: int) -> Optional[Tuple[int,int,int,int]]:
        """
        Returns (band_a_id, band_b_id, split_a_pct, split_b_pct) if a collab row exists.
        """
        try:
            cur.execute("""
                SELECT band_a_id, band_b_id, split_a_pct, split_b_pct
                FROM collaborations
                WHERE work_type = ? AND work_id = ?
            """, (work_type, work_id))
            row = cur.fetchone()
            if row:
                return int(row[0]), int(row[1]), int(row[2]), int(row[3])
        except Exception:
            return None
        return None

    def _emit_line(
        self,
        cur,
        run_id: int,
        work_type: str,
        work_id: Optional[int],
        band_id: Optional[int],
        collaborator_band_id: Optional[int],
        source: str,
        amount_cents: int,
        meta: Optional[Dict[str, Any]] = None,
        region: str = "global",
    ) -> None:
        cur.execute(
            """
            INSERT INTO royalty_run_lines (run_id, region, work_type, work_id, band_id, collaborator_band_id, source, amount_cents, meta_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                region,
                work_type,
                work_id,
                band_id,
                collaborator_band_id,
                source,
                int(amount_cents),
                json.dumps(meta) if meta else None,
            ),
        )

    # -------- channels --------
    def _process_streams(self, cur, run_id: int, window: RunWindow, region: str) -> None:
        if not self._table_exists(cur, "streams"):
            return
        region_sql, params = self._region_filter(cur, "streams", region)
        cur.execute(
            f"""
            WITH capped AS (
              SELECT song_id, date(created_at) AS d, user_id, MIN(COUNT(*), {DAILY_STREAM_CAP_PER_USER_PER_SONG}) AS capped_plays
              FROM streams
              WHERE datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?) {region_sql}
              GROUP BY song_id, d, user_id
            ),
            sum_by_song AS (
              SELECT song_id, SUM(capped_plays) AS total_plays
              FROM capped
              GROUP BY song_id
            )
            SELECT song_id, total_plays FROM sum_by_song
        """,
            (f"{window.start} 00:00:00", f"{window.end} 23:59:59", *params),
        )
        rows = cur.fetchall()
        for song_id, plays in rows:
            plays = int(plays or 0)
            microcents = plays * STREAM_RATE_MICROCENTS
            cents = microcents // 100
            if cents <= 0:
                continue
            split = self._collab_split(cur, "song", song_id)
            if split:
                a_id, b_id, a_pct, b_pct = split
                a_amt = cents * a_pct // 100
                b_amt = cents - a_amt
                self._emit_line(
                    cur,
                    run_id,
                    "song",
                    song_id,
                    a_id,
                    b_id,
                    "streams",
                    a_amt,
                    {"plays": plays, "split": f"{a_pct}/{b_pct}"},
                    region=region,
                )
                self._emit_line(
                    cur,
                    run_id,
                    "song",
                    song_id,
                    b_id,
                    a_id,
                    "streams",
                    b_amt,
                    {"plays": plays, "split": f"{a_pct}/{b_pct}"},
                    region=region,
                )
            else:
                band_id = self._owner_band_for_work(cur, "song", song_id)
                self._emit_line(
                    cur,
                    run_id,
                    "song",
                    song_id,
                    band_id,
                    None,
                    "streams",
                    cents,
                    {"plays": plays},
                    region=region,
                )

    def _process_digital(self, cur, run_id: int, window: RunWindow, region: str) -> None:
        if not self._table_exists(cur, "digital_sales"):
            return
        region_sql, params = self._region_filter(cur, "digital_sales", region)
        cur.execute(
            """
            SELECT work_type, work_id, SUM(price_cents) as revenue_cents, COUNT(*) as cnt
            FROM digital_sales
            WHERE datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?){} 
            GROUP BY work_type, work_id
        """.format(region_sql),
            (f"{window.start} 00:00:00", f"{window.end} 23:59:59", *params),
        )
        for work_type, work_id, revenue_cents, cnt in cur.fetchall():
            work_type = (work_type or "").lower()
            revenue_cents = int(revenue_cents or 0)
            if revenue_cents <= 0:
                continue
            if work_type not in ("song", "album"):
                work_type = "misc"
            split = self._collab_split(cur, work_type, int(work_id)) if work_type in ("song","album") else None
            meta = {"count": int(cnt)}
            if split and work_type in ("song","album"):
                a_id, b_id, a_pct, b_pct = split
                a_amt = revenue_cents * a_pct // 100
                b_amt = revenue_cents - a_amt
                self._emit_line(
                    cur,
                    run_id,
                    work_type,
                    int(work_id),
                    a_id,
                    b_id,
                    "digital",
                    a_amt,
                    {**meta, "split": f"{a_pct}/{b_pct}"},
                    region=region,
                )
                self._emit_line(
                    cur,
                    run_id,
                    work_type,
                    int(work_id),
                    b_id,
                    a_id,
                    "digital",
                    b_amt,
                    {**meta, "split": f"{a_pct}/{b_pct}"},
                    region=region,
                )
            else:
                band_id = self._owner_band_for_work(cur, work_type, int(work_id)) if work_type in ("song","album") else None
                self._emit_line(
                    cur,
                    run_id,
                    work_type,
                    int(work_id),
                    band_id,
                    None,
                    "digital",
                    revenue_cents,
                    meta,
                    region=region,
                )

    def _process_vinyl(self, cur, run_id: int, window: RunWindow, region: str) -> None:
        needed = ["vinyl_order_items", "vinyl_orders", "vinyl_skus"]
        if not all(self._table_exists(cur, t) for t in needed):
            return
        region_sql, params = self._region_filter(cur, "vinyl_orders", region, alias="o")
        cur.execute(
            """
            SELECT s.album_id, SUM(oi.unit_price_cents * (oi.qty - oi.refunded_qty)) AS revenue_cents,
                   SUM(oi.qty - oi.refunded_qty) as units
            FROM vinyl_order_items oi
            JOIN vinyl_orders o ON o.id = oi.order_id
            JOIN vinyl_skus s ON s.id = oi.sku_id
            WHERE o.status = 'confirmed'
              AND datetime(o.created_at) >= datetime(?)
              AND datetime(o.created_at) <= datetime(?){}
            GROUP BY s.album_id
        """.format(region_sql),
            (f"{window.start} 00:00:00", f"{window.end} 23:59:59", *params),
        )
        for album_id, revenue_cents, units in cur.fetchall():
            revenue_cents = int(revenue_cents or 0)
            if revenue_cents <= 0:
                continue
            split = self._collab_split(cur, "album", int(album_id))
            meta = {"units": int(units)}
            if split:
                a_id, b_id, a_pct, b_pct = split
                a_amt = revenue_cents * a_pct // 100
                b_amt = revenue_cents - a_amt
                self._emit_line(
                    cur,
                    run_id,
                    "album",
                    int(album_id),
                    a_id,
                    b_id,
                    "vinyl",
                    a_amt,
                    {**meta, "split": f"{a_pct}/{b_pct}"},
                    region=region,
                )
                self._emit_line(
                    cur,
                    run_id,
                    "album",
                    int(album_id),
                    b_id,
                    a_id,
                    "vinyl",
                    b_amt,
                    {**meta, "split": f"{a_pct}/{b_pct}"},
                    region=region,
                )
            else:
                band_id = self._owner_band_for_work(cur, "album", int(album_id))
                self._emit_line(
                    cur,
                    run_id,
                    "album",
                    int(album_id),
                    band_id,
                    None,
                    "vinyl",
                    revenue_cents,
                    meta,
                    region=region,
                )

    def _process_sponsorships(self, cur, run_id: int, window: RunWindow, region: str) -> None:
        """Aggregate sponsorship ad events into royalty lines."""
        needed = ["sponsorship_ad_events", "venue_sponsorships"]
        if not all(self._table_exists(cur, t) for t in needed):
            return
        region_sql, params = self._region_filter(cur, "sponsorship_ad_events", region, alias="e")
        if not region_sql:
            region_sql, params = self._region_filter(cur, "venue_sponsorships", region, alias="vs")
        cur.execute(
            """
            SELECT vs.venue_id, COUNT(*) as impressions
            FROM sponsorship_ad_events e
            JOIN venue_sponsorships vs ON vs.id = e.sponsorship_id
            WHERE e.event_type = 'impression'
              AND datetime(e.occurred_at) >= datetime(?)
              AND datetime(e.occurred_at) <= datetime(?)
              AND vs.is_active = 1{}
            GROUP BY vs.venue_id
            """.format(region_sql),
            (f"{window.start} 00:00:00", f"{window.end} 23:59:59", *params),
        )
        for venue_id, impressions in cur.fetchall():
            impressions = int(impressions or 0)
            if impressions <= 0:
                continue
            gross = impressions * SPONSOR_IMPRESSION_RATE_CENTS
            venue_share = gross * SPONSOR_PAYOUT_SPLIT.get("venue", 0) // 100
            if venue_share <= 0:
                continue
            self._emit_line(
                cur,
                run_id,
                "venue",
                int(venue_id),
                None,
                None,
                "sponsorship",
                venue_share,
                {"impressions": impressions},
                region=region,
            )

    # -------- public API --------
    def _run_single_region(self, period_start: str, period_end: str, region: str) -> Dict[str, Any]:
        window = RunWindow(period_start, period_end)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            self.ensure_schema()
            try:
                cur.execute("BEGIN IMMEDIATE")
                run_id = self._create_run(cur, window, region)
                conn.commit()
            except Exception:
                conn.rollback()
                raise

            stats = {
                "streams": 0,
                "digital": 0,
                "vinyl": 0,
                "sponsorship": 0,
                "run_id": run_id,
                "region": region,
            }
            try:
                cur.execute("BEGIN IMMEDIATE")
                before = self._count_lines(cur, run_id)
                self._process_streams(cur, run_id, window, region)
                after = self._count_lines(cur, run_id)
                stats["streams"] = after - before

                before = self._count_lines(cur, run_id)
                self._process_digital(cur, run_id, window, region)
                after = self._count_lines(cur, run_id)
                stats["digital"] = after - before

                before = self._count_lines(cur, run_id)
                self._process_vinyl(cur, run_id, window, region)
                after = self._count_lines(cur, run_id)
                stats["vinyl"] = after - before

                before = self._count_lines(cur, run_id)
                self._process_sponsorships(cur, run_id, window, region)
                after = self._count_lines(cur, run_id)
                stats["sponsorship"] = after - before

                self._complete_run(cur, run_id, notes=None)
                conn.commit()
                ROYALTY_JOB_SUCCESS.labels(region).inc()
            except Exception as e:
                conn.rollback()
                cur.execute("BEGIN IMMEDIATE")
                self._fail_run(cur, run_id, err=str(e))
                conn.commit()
                ROYALTY_JOB_FAILURES.labels(region).inc()
                raise
            return stats

    def run_royalties(
        self,
        period_start: str,
        period_end: str,
        regions: Optional[List[str]] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        regions = regions or ["global"]
        results: Dict[str, Any] = {}
        for region in regions:
            attempt = 0
            while attempt < max_retries:
                attempt += 1
                try:
                    results[region] = self._run_single_region(period_start, period_end, region)
                    break
                except Exception:
                    if attempt >= max_retries:
                        results[region] = {"error": "failed"}
        return results

    def _count_lines(self, cur, run_id: int) -> int:
        cur.execute("SELECT COUNT(*) FROM royalty_run_lines WHERE run_id = ?", (run_id,))
        return int(cur.fetchone()[0])
