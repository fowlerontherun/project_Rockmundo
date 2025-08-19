# File: backend/services/analytics_service.py
"""
Admin Analytics Service
-----------------------
Read-only KPIs and leaderboards for streams, digital sales, vinyl, tickets,
and royalties. Queries are resilient: if a table doesn't exist yet, that
section is simply skipped so the API still returns useful data.
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

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
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            res = {
                "streams": {"plays": 0},
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
