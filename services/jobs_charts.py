# File: backend/services/jobs_charts.py
"""
Charts Jobs Service
Computes daily/weekly charts for:
- streams_song: per-song play counts (with per-user/day cap if desired)
- digital_song: per-song digital revenue (sum price_cents)
- digital_album: per-album digital revenue (if you sell albums digitally)
- vinyl_album: per-album vinyl revenue (order items * unit price - refunded)
- combined_song: normalized combination of streams + digital revenue for songs
- combined_album: normalized combination of digital + vinyl revenue for albums

Normalization (adjustable constants):
- STREAMS_PLAY_WEIGHT = 0.01   => every 100 plays ~ 1.0 point
- REVENUE_CENTS_WEIGHT = 0.01  => every $1.00 (100 cents) ~ 1.0 point

You can tune these weights later or make them config-driven.
"""

import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

STREAMS_PLAY_WEIGHT = 0.01
REVENUE_CENTS_WEIGHT = 0.01
DAILY_STREAM_CAP_PER_USER_PER_SONG = 50  # keep in sync with royalty job if needed

@dataclass
class Window:
    start: str  # 'YYYY-MM-DD'
    end: str    # 'YYYY-MM-DD'

class ChartsJobError(Exception):
    pass

class ChartsJobsService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)

    # -------- schema --------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS chart_snapshots (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              chart_type TEXT NOT NULL,
              period TEXT NOT NULL,
              period_start TEXT NOT NULL,
              period_end TEXT NOT NULL,
              country_code TEXT,
              region TEXT DEFAULT 'global',
              rank INTEGER NOT NULL,
              work_type TEXT NOT NULL,
              work_id INTEGER NOT NULL,
              band_id INTEGER,
              title TEXT,
              metric_value REAL NOT NULL,
              source_notes TEXT,
              created_at TEXT DEFAULT (datetime('now')),
              UNIQUE(chart_type, period, period_start, country_code, rank)
            )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS ix_charts_period ON chart_snapshots(period, period_start)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_charts_work ON chart_snapshots(work_type, work_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_charts_region ON chart_snapshots(region)")
            cur.execute("CREATE INDEX IF NOT EXISTS ix_charts_country ON chart_snapshots(country_code)")
            conn.commit()

    # -------- utilities --------
    def _table_exists(self, cur, name: str) -> bool:
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None

    def _owner_band_and_title(self, cur, work_type: str, work_id: int) -> Tuple[Optional[int], Optional[str]]:
        try:
            if work_type == "song":
                cur.execute("SELECT band_id, title FROM songs WHERE id = ?", (work_id,))
            else:
                cur.execute("SELECT band_id, title FROM albums WHERE id = ?", (work_id,))
            row = cur.fetchone()
            if row:
                return (int(row[0]) if row[0] is not None else None, row[1])
        except Exception:
            pass
        return (None, None)

    def _clear_period(self, cur, chart_type: str, period: str, window: Window) -> None:
        cur.execute(
            """
            DELETE FROM chart_snapshots
            WHERE chart_type = ? AND period = ? AND period_start = ?
            """,
            (chart_type, period, window.start),
        )

    def _insert_rows(
        self,
        cur,
        chart_type: str,
        period: str,
        window: Window,
        rows: List[Tuple[Optional[str], str, int, float, str]],
    ):
        """
        rows: list of (country_code, work_type, work_id, metric_value, source_notes)
        """
        ranks: Dict[Optional[str], int] = defaultdict(lambda: 1)
        for country_code, work_type, work_id, metric_value, notes in rows:
            band_id, title = self._owner_band_and_title(cur, work_type, work_id)
            rank = ranks[country_code]
            cur.execute(
                """
                INSERT INTO chart_snapshots (
                    chart_type, period, period_start, period_end,
                    country_code, rank, work_type, work_id, band_id,
                    title, metric_value, source_notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chart_type,
                    period,
                    window.start,
                    window.end,
                    country_code,
                    rank,
                    work_type,
                    work_id,
                    band_id,
                    title,
                    float(metric_value),
                    notes,
                ),
            )
            ranks[country_code] += 1

    # -------- channel aggregations --------
    def _has_column(self, cur, table: str, column: str) -> bool:
        cur.execute(f"PRAGMA table_info({table})")
        return any(row[1].lower() == column.lower() for row in cur.fetchall())

    def _aggregate_streams_song(
        self, cur, window: Window
    ) -> List[Tuple[Optional[str], str, int, float, str]]:
        if not self._table_exists(cur, "streams"):
            return []

        country_col = None
        if self._has_column(cur, "streams", "country_code"):
            country_col = "country_code"
        elif self._has_column(cur, "streams", "country"):
            country_col = "country"

        if country_col:
            cur.execute(
                f"""
                WITH capped AS (
                  SELECT song_id, {country_col} AS cc, date(created_at) AS d, user_id,
                         MIN(COUNT(*), {DAILY_STREAM_CAP_PER_USER_PER_SONG}) AS capped_plays
                  FROM streams
                  WHERE datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?)
                  GROUP BY song_id, cc, d, user_id
                ), tot AS (
                  SELECT cc AS country_code, song_id, SUM(capped_plays) AS plays
                  FROM capped
                  GROUP BY cc, song_id
                )
                SELECT country_code, song_id, plays FROM tot
                """,
                (f"{window.start} 00:00:00", f"{window.end} 23:59:59"),
            )
            data = cur.fetchall()
            grouped: Dict[Optional[str], List[Tuple[int, float]]] = defaultdict(list)
            for cc, song_id, plays in data:
                grouped[cc].append((int(song_id), float(plays)))
            out: List[Tuple[Optional[str], str, int, float, str]] = []
            for cc, vals in grouped.items():
                vals.sort(key=lambda x: (-x[1], x[0]))
                for song_id, plays in vals[:100]:
                    out.append((cc, "song", song_id, plays, "plays"))
            return out
        else:
            cur.execute(
                f"""
                WITH capped AS (
                  SELECT song_id, date(created_at) AS d, user_id,
                         MIN(COUNT(*), {DAILY_STREAM_CAP_PER_USER_PER_SONG}) AS capped_plays
                  FROM streams
                  WHERE datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?)
                  GROUP BY song_id, d, user_id
                ), tot AS (
                  SELECT song_id, SUM(capped_plays) AS plays FROM capped GROUP BY song_id
                )
                SELECT song_id, plays FROM tot ORDER BY plays DESC, song_id ASC LIMIT 100
                """,
                (f"{window.start} 00:00:00", f"{window.end} 23:59:59"),
            )
            rows = cur.fetchall()
            return [(None, "song", int(song_id), float(plays), "plays") for (song_id, plays) in rows]

    def _aggregate_digital_song(
        self, cur, window: Window
    ) -> List[Tuple[Optional[str], str, int, float, str]]:
        if not self._table_exists(cur, "digital_sales"):
            return []

        country_col = None
        if self._has_column(cur, "digital_sales", "country_code"):
            country_col = "country_code"
        elif self._has_column(cur, "digital_sales", "country"):
            country_col = "country"

        if country_col:
            cur.execute(
                f"""
                SELECT {country_col} AS cc, work_id, SUM(price_cents) as cents
                FROM digital_sales
                WHERE work_type = 'song'
                  AND datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?)
                GROUP BY cc, work_id
                """,
                (f"{window.start} 00:00:00", f"{window.end} 23:59:59"),
            )
            data = cur.fetchall()
            grouped: Dict[Optional[str], List[Tuple[int, float]]] = defaultdict(list)
            for cc, wid, cents in data:
                grouped[cc].append((int(wid), float(cents)))
            out: List[Tuple[Optional[str], str, int, float, str]] = []
            for cc, vals in grouped.items():
                vals.sort(key=lambda x: (-x[1], x[0]))
                for wid, cents in vals[:100]:
                    out.append((cc, "song", wid, cents, "digital_cents"))
            return out
        else:
            cur.execute(
                """
                SELECT work_id, SUM(price_cents) as cents
                FROM digital_sales
                WHERE work_type = 'song'
                  AND datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?)
                GROUP BY work_id
                ORDER BY cents DESC, work_id ASC
                LIMIT 100
                """,
                (f"{window.start} 00:00:00", f"{window.end} 23:59:59"),
            )
            return [
                (None, "song", int(work_id), float(cents), "digital_cents")
                for (work_id, cents) in cur.fetchall()
            ]

    def _aggregate_digital_album(
        self, cur, window: Window
    ) -> List[Tuple[Optional[str], str, int, float, str]]:
        if not self._table_exists(cur, "digital_sales"):
            return []

        country_col = None
        if self._has_column(cur, "digital_sales", "country_code"):
            country_col = "country_code"
        elif self._has_column(cur, "digital_sales", "country"):
            country_col = "country"

        if country_col:
            cur.execute(
                f"""
                SELECT {country_col} AS cc, work_id, SUM(price_cents) as cents
                FROM digital_sales
                WHERE work_type = 'album'
                  AND datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?)
                GROUP BY cc, work_id
                """,
                (f"{window.start} 00:00:00", f"{window.end} 23:59:59"),
            )
            data = cur.fetchall()
            grouped: Dict[Optional[str], List[Tuple[int, float]]] = defaultdict(list)
            for cc, wid, cents in data:
                grouped[cc].append((int(wid), float(cents)))
            out: List[Tuple[Optional[str], str, int, float, str]] = []
            for cc, vals in grouped.items():
                vals.sort(key=lambda x: (-x[1], x[0]))
                for wid, cents in vals[:100]:
                    out.append((cc, "album", wid, cents, "digital_cents"))
            return out
        else:
            cur.execute(
                """
                SELECT work_id, SUM(price_cents) as cents
                FROM digital_sales
                WHERE work_type = 'album'
                  AND datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?)
                GROUP BY work_id
                ORDER BY cents DESC, work_id ASC
                LIMIT 100
                """,
                (f"{window.start} 00:00:00", f"{window.end} 23:59:59"),
            )
            return [
                (None, "album", int(work_id), float(cents), "digital_cents")
                for (work_id, cents) in cur.fetchall()
            ]

    def _aggregate_vinyl_album(
        self, cur, window: Window
    ) -> List[Tuple[Optional[str], str, int, float, str]]:
        needed = ["vinyl_order_items", "vinyl_orders", "vinyl_skus"]
        if not all(self._table_exists(cur, t) for t in needed):
            return []

        country_col = None
        if self._has_column(cur, "vinyl_orders", "country_code"):
            country_col = "country_code"
        elif self._has_column(cur, "vinyl_orders", "country"):
            country_col = "country"

        if country_col:
            cur.execute(
                f"""
                SELECT o.{country_col} AS cc, s.album_id,
                       SUM(oi.unit_price_cents * (oi.qty - oi.refunded_qty)) as cents
                FROM vinyl_order_items oi
                JOIN vinyl_orders o ON o.id = oi.order_id
                JOIN vinyl_skus s ON s.id = oi.sku_id
                WHERE o.status = 'confirmed'
                  AND datetime(o.created_at) >= datetime(?)
                  AND datetime(o.created_at) <= datetime(?)
                GROUP BY cc, s.album_id
                """,
                (f"{window.start} 00:00:00", f"{window.end} 23:59:59"),
            )
            data = cur.fetchall()
            grouped: Dict[Optional[str], List[Tuple[int, float]]] = defaultdict(list)
            for cc, album_id, cents in data:
                grouped[cc].append((int(album_id), float(cents)))
            out: List[Tuple[Optional[str], str, int, float, str]] = []
            for cc, vals in grouped.items():
                vals.sort(key=lambda x: (-x[1], x[0]))
                for aid, cents in vals[:100]:
                    out.append((cc, "album", aid, cents, "vinyl_cents"))
            return out
        else:
            cur.execute(
                """
                SELECT s.album_id, SUM(oi.unit_price_cents * (oi.qty - oi.refunded_qty)) as cents
                FROM vinyl_order_items oi
                JOIN vinyl_orders o ON o.id = oi.order_id
                JOIN vinyl_skus s ON s.id = oi.sku_id
                WHERE o.status = 'confirmed'
                  AND datetime(o.created_at) >= datetime(?)
                  AND datetime(o.created_at) <= datetime(?)
                GROUP BY s.album_id
                ORDER BY cents DESC, s.album_id ASC
                LIMIT 100
                """,
                (f"{window.start} 00:00:00", f"{window.end} 23:59:59"),
            )
            return [
                (None, "album", int(album_id), float(cents), "vinyl_cents")
                for (album_id, cents) in cur.fetchall()
            ]

    def _aggregate_combined_song(
        self, cur, window: Window
    ) -> List[Tuple[Optional[str], str, int, float, str]]:
        # streams + digital revenue
        streams = {sid: float(plays)*STREAMS_PLAY_WEIGHT for sid, plays in self._map_streams(cur, window).items()}
        digital = {sid: float(cents)*REVENUE_CENTS_WEIGHT for sid, cents in self._map_digital(cur, window, "song").items()}
        keys = set(streams) | set(digital)
        combined: List[Tuple[Optional[str], str, int, float, str]] = []
        for k in keys:
            combined.append((None, "song", int(k), float(streams.get(k,0.0)+digital.get(k,0.0)), "score(streams+digital)"))
        combined.sort(key=lambda x: (-x[3], x[2]))
        return combined[:100]

    def _aggregate_combined_album(
        self, cur, window: Window
    ) -> List[Tuple[Optional[str], str, int, float, str]]:
        digital = {aid: float(cents)*REVENUE_CENTS_WEIGHT for aid, cents in self._map_digital(cur, window, "album").items()}
        vinyl = {aid: float(cents)*REVENUE_CENTS_WEIGHT for aid, cents in self._map_vinyl(cur, window).items()}
        keys = set(digital) | set(vinyl)
        rows: List[Tuple[Optional[str], str, int, float, str]] = []
        for k in keys:
            rows.append((None, "album", int(k), float(digital.get(k,0.0)+vinyl.get(k,0.0)), "score(digital+vinyl)"))
        rows.sort(key=lambda x: (-x[3], x[2]))
        return rows[:100]

    # maps for combined
    def _map_streams(self, cur, window: Window) -> Dict[int,int]:
        if not self._table_exists(cur, "streams"):
            return {}
        cur.execute(f"""
            WITH capped AS (
              SELECT song_id, date(created_at) AS d, user_id, MIN(COUNT(*), {DAILY_STREAM_CAP_PER_USER_PER_SONG}) AS capped_plays
              FROM streams
              WHERE datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?)
              GROUP BY song_id, d, user_id
            )
            SELECT song_id, SUM(capped_plays) AS plays
            FROM capped
            GROUP BY song_id
        """, (f"{window.start} 00:00:00", f"{window.end} 23:59:59"))
        return {int(song_id): int(plays or 0) for (song_id, plays) in cur.fetchall()}

    def _map_digital(self, cur, window: Window, work_type: str) -> Dict[int,int]:
        if not self._table_exists(cur, "digital_sales"):
            return {}
        cur.execute("""
            SELECT work_id, SUM(price_cents) AS cents
            FROM digital_sales
            WHERE work_type = ?
              AND datetime(created_at) >= datetime(?) AND datetime(created_at) <= datetime(?)
            GROUP BY work_id
        """, (work_type, f"{window.start} 00:00:00", f"{window.end} 23:59:59"))
        return {int(work_id): int(cents or 0) for (work_id, cents) in cur.fetchall()}

    def _map_vinyl(self, cur, window: Window) -> Dict[int,int]:
        needed = ["vinyl_order_items","vinyl_orders","vinyl_skus"]
        if not all(self._table_exists(cur, t) for t in needed):
            return {}
        cur.execute("""
            SELECT s.album_id, SUM(oi.unit_price_cents * (oi.qty - oi.refunded_qty)) as cents
            FROM vinyl_order_items oi
            JOIN vinyl_orders o ON o.id = oi.order_id
            JOIN vinyl_skus s ON s.id = oi.sku_id
            WHERE o.status = 'confirmed'
              AND datetime(o.created_at) >= datetime(?)
              AND datetime(o.created_at) <= datetime(?)
            GROUP BY s.album_id
        """, (f"{window.start} 00:00:00", f"{window.end} 23:59:59"))
        return {int(album_id): int(cents or 0) for (album_id, cents) in cur.fetchall()}

    # -------- public API --------
    def run_daily(self, date_str: str) -> Dict[str, Any]:
        """
        Compute charts for a single day (UTC). date_str='YYYY-MM-DD'.
        """
        w = Window(start=date_str, end=date_str)
        return self._run("daily", w)

    def run_weekly(self, week_end_date: str) -> Dict[str, Any]:
        """
        Compute charts for week Monday..Sunday. Provide week_end_date as a Sunday (YYYY-MM-DD).
        """
        end_dt = datetime.strptime(week_end_date, "%Y-%m-%d")
        start_dt = end_dt - timedelta(days=6)
        w = Window(start=start_dt.strftime("%Y-%m-%d"), end=end_dt.strftime("%Y-%m-%d"))
        return self._run("weekly", w)

    def _run(self, period: str, window: Window) -> Dict[str, Any]:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # streams_song
            rows = self._aggregate_streams_song(cur, window)
            self._clear_period(cur, "streams_song", period, window)
            self._insert_rows(cur, "streams_song", period, window, rows)

            # digital_song
            rows = self._aggregate_digital_song(cur, window)
            self._clear_period(cur, "digital_song", period, window)
            self._insert_rows(cur, "digital_song", period, window, rows)

            # digital_album
            rows = self._aggregate_digital_album(cur, window)
            self._clear_period(cur, "digital_album", period, window)
            self._insert_rows(cur, "digital_album", period, window, rows)

            # vinyl_album
            rows = self._aggregate_vinyl_album(cur, window)
            self._clear_period(cur, "vinyl_album", period, window)
            self._insert_rows(cur, "vinyl_album", period, window, rows)

            # combined_song
            rows = self._aggregate_combined_song(cur, window)
            self._clear_period(cur, "combined_song", period, window)
            self._insert_rows(cur, "combined_song", period, window, rows)

            # combined_album
            rows = self._aggregate_combined_album(cur, window)
            self._clear_period(cur, "combined_album", period, window)
            self._insert_rows(cur, "combined_album", period, window, rows)

            conn.commit()
            return {"ok": True, "period": period, "start": window.start, "end": window.end}
