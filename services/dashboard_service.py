# File: backend/services/dashboard_service.py
from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from utils.db import get_conn


class DashboardService:
    """
    Aggregates small, fast queries to power the Player Dashboard cards:
      - next_show: the user's (or band's) next upcoming tour stop
      - badge: unread mail and notifications
      - pulse: compact world pulse snippet (rank + pct_change + trend) for top N
      - music: recent sales/streams totals (last 7 and 30 days)
    This service is resilient: if a table is missing, it returns an empty section rather than erroring.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    # ---------- helpers ----------
    def _table_exists(self, conn: sqlite3.Connection, name: str) -> bool:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
        return cur.fetchone() is not None

    # ---------- public API ----------
    def summary(self, user_id: int, band_id: Optional[int] = None, top_n: int = 10) -> Dict[str, Any]:
        with get_conn(self.db_path) as conn:
            return {
                "next_show": self._next_show(conn, band_id or 0),
                "badge": self._badge(conn, user_id),
                "pulse": self._pulse_snippet(conn, top_n=top_n),
                "music": self._music_totals(conn),
                "chart_regions": self._chart_region_breakdown(conn),
            }

    # ---------- sections ----------
    def _next_show(self, conn: sqlite3.Connection, band_id: int) -> Dict[str, Any]:
        if not (self._table_exists(conn, "tour_stops") and self._table_exists(conn, "tours") and self._table_exists(conn, "venues")):
            return {}
        cur = conn.cursor()
        # If band_id is 0 (unknown), just show the earliest upcoming stop globally.
        cur.execute(
            """
            SELECT ts.id AS stop_id, t.id AS tour_id, t.name AS tour_name, v.name AS venue_name,
                   v.city, v.country, ts.date_start, ts.date_end, ts.status
            FROM tour_stops ts
            JOIN tours t ON t.id = ts.tour_id
            JOIN venues v ON v.id = ts.venue_id
            WHERE ts.status IN ('pending','confirmed')
              AND date(ts.date_end) >= date('now')
              AND (? = 0 OR t.band_id = ?)
            ORDER BY date(ts.date_start) ASC, ts.order_index ASC
            LIMIT 1
            """,
            (band_id, band_id),
        )
        row = cur.fetchone()
        return dict(row) if row else {}

    def _badge(self, conn: sqlite3.Connection, user_id: int) -> Dict[str, int]:
        mail = 0
        notif = 0
        if self._table_exists(conn, "mail_participants") and self._table_exists(conn, "mail_messages"):
            cur = conn.cursor()
            cur.execute(
                """
                SELECT SUM(CASE WHEN m.id > p.last_read_message_id AND m.sender_id != p.user_id THEN 1 ELSE 0 END)
                FROM mail_participants p
                JOIN mail_messages m ON m.thread_id = p.thread_id
                WHERE p.user_id = ?
                """,
                (user_id,),
            )
            mail = int(cur.fetchone()[0] or 0)
        if self._table_exists(conn, "notifications"):
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND read_at IS NULL", (user_id,))
            notif = int(cur.fetchone()[0] or 0)
        return {"mail": mail, "notifications": notif}

    def _pulse_snippet(self, conn: sqlite3.Connection, top_n: int = 10) -> List[Dict[str, Any]]:
        # Prefer cached weekly view/table if available
        table_candidates = [
            "world_pulse_weekly_cache",
            "world_pulse_rankings",
            "world_pulse_metrics",
        ]
        table = next((t for t in table_candidates if self._table_exists(conn, t)), None)
        if not table:
            return []
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        cols = {row[1].lower() for row in cur.fetchall()}
        name_cols = [c for c in ("name", "artist", "band_name") if c in cols]
        rank_cols = [c for c in ("rank", "ranking", "position") if c in cols]
        pct_cols = [c for c in ("pct_change", "change_pct", "delta_pct") if c in cols]
        if not rank_cols:
            return []
        name_expr = (
            "COALESCE(" + ",".join(name_cols) + ")" if len(name_cols) > 1 else name_cols[0]
        ) if name_cols else "''"
        rank_expr = (
            "COALESCE(" + ",".join(rank_cols) + ")" if len(rank_cols) > 1 else rank_cols[0]
        )
        pct_base = (
            "COALESCE(" + ",".join(pct_cols + ["0.0"]) + ")"
            if pct_cols
            else "0.0"
        )
        query = f"""
            SELECT
                {name_expr} AS name,
                {rank_expr} AS rank,
                {pct_base} AS pct_change,
                CASE WHEN {pct_base} > 0 THEN '↑'
                     WHEN {pct_base} < 0 THEN '↓'
                     ELSE '→' END AS trend
            FROM {table}
            ORDER BY {rank_expr} ASC
            LIMIT ?
        """
        try:
            cur.execute(query, (top_n,))
            rows = [dict(r) for r in cur.fetchall()]
        except Exception:
            rows = []
        return rows

    def _music_totals(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        out: Dict[str, Any] = {"last_7d": {}, "last_30d": {}}
        # digital sales
        if self._table_exists(conn, "sales_digital"):
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    SUM(CASE WHEN date(created_at) >= date('now','-7 day') THEN quantity ELSE 0 END) AS qty_7d,
                    SUM(CASE WHEN date(created_at) >= date('now','-30 day') THEN quantity ELSE 0 END) AS qty_30d,
                    SUM(CASE WHEN date(created_at) >= date('now','-7 day') THEN revenue ELSE 0 END) AS rev_7d,
                    SUM(CASE WHEN date(created_at) >= date('now','-30 day') THEN revenue ELSE 0 END) AS rev_30d
                FROM sales_digital
            """)
            r = cur.fetchone()
            out["last_7d"]["digital_sales_qty"] = int(r["qty_7d"] or 0)
            out["last_30d"]["digital_sales_qty"] = int(r["qty_30d"] or 0)
            out["last_7d"]["digital_revenue"] = float(r["rev_7d"] or 0.0)
            out["last_30d"]["digital_revenue"] = float(r["rev_30d"] or 0.0)
        # vinyl sales
        if self._table_exists(conn, "sales_vinyl"):
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    SUM(CASE WHEN date(created_at) >= date('now','-7 day') THEN quantity ELSE 0 END) AS qty_7d,
                    SUM(CASE WHEN date(created_at) >= date('now','-30 day') THEN quantity ELSE 0 END) AS qty_30d,
                    SUM(CASE WHEN date(created_at) >= date('now','-7 day') THEN revenue ELSE 0 END) AS rev_7d,
                    SUM(CASE WHEN date(created_at) >= date('now','-30 day') THEN revenue ELSE 0 END) AS rev_30d
                FROM sales_vinyl
            """)
            r = cur.fetchone()
            out["last_7d"]["vinyl_sales_qty"] = int(r["qty_7d"] or 0)
            out["last_30d"]["vinyl_sales_qty"] = int(r["qty_30d"] or 0)
            out["last_7d"]["vinyl_revenue"] = float(r["rev_7d"] or 0.0)
            out["last_30d"]["vinyl_revenue"] = float(r["rev_30d"] or 0.0)
        # streams
        if self._table_exists(conn, "streams"):
            cur = conn.cursor()
            cur.execute("""
                SELECT
                    SUM(CASE WHEN date(created_at) >= date('now','-7 day') THEN count ELSE 0 END) AS c7,
                    SUM(CASE WHEN date(created_at) >= date('now','-30 day') THEN count ELSE 0 END) AS c30
                FROM streams
            """)
            r = cur.fetchone()
            out["last_7d"]["streams"] = int(r["c7"] or 0)
            out["last_30d"]["streams"] = int(r["c30"] or 0)
        return out

    def _chart_region_breakdown(self, conn: sqlite3.Connection) -> Dict[str, int]:
        if not self._table_exists(conn, "chart_snapshots"):
            return {}
        cur = conn.cursor()
        cur.execute(
            "SELECT region, MAX(period_start) AS latest FROM chart_snapshots GROUP BY region"
        )
        rows = cur.fetchall()
        out: Dict[str, int] = {}
        for region, latest in rows:
            cur.execute(
                "SELECT COUNT(*) FROM chart_snapshots WHERE region=? AND period_start=?",
                (region, latest),
            )
            out[region] = int(cur.fetchone()[0] or 0)
        return out
