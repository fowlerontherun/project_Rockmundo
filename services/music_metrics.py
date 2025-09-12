# File: backend/services/music_metrics.py
from typing import Optional, Dict, Any
from utils.db import get_conn

class MusicMetricsService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def totals(self) -> Dict[str, Any]:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT
                  SUM(CASE WHEN event_type='sale_digital' AND date(created_at) >= date('now','-7 day') THEN quantity ELSE 0 END) AS dg_qty_7,
                  SUM(CASE WHEN event_type='sale_digital' AND date(created_at) >= date('now','-30 day') THEN quantity ELSE 0 END) AS dg_qty_30,
                  SUM(CASE WHEN event_type='sale_digital' AND date(created_at) >= date('now','-7 day') THEN revenue ELSE 0 END) AS dg_rev_7,
                  SUM(CASE WHEN event_type='sale_digital' AND date(created_at) >= date('now','-30 day') THEN revenue ELSE 0 END) AS dg_rev_30,
                  SUM(CASE WHEN event_type='sale_vinyl' AND date(created_at) >= date('now','-7 day') THEN quantity ELSE 0 END) AS vn_qty_7,
                  SUM(CASE WHEN event_type='sale_vinyl' AND date(created_at) >= date('now','-30 day') THEN quantity ELSE 0 END) AS vn_qty_30,
                  SUM(CASE WHEN event_type='sale_vinyl' AND date(created_at) >= date('now','-7 day') THEN revenue ELSE 0 END) AS vn_rev_7,
                  SUM(CASE WHEN event_type='sale_vinyl' AND date(created_at) >= date('now','-30 day') THEN revenue ELSE 0 END) AS vn_rev_30,
                  SUM(CASE WHEN event_type='stream' AND date(created_at) >= date('now','-7 day') THEN quantity ELSE 0 END) AS st_cnt_7,
                  SUM(CASE WHEN event_type='stream' AND date(created_at) >= date('now','-30 day') THEN quantity ELSE 0 END) AS st_cnt_30
                FROM music_events
            """)
            r = cur.fetchone()
            return {
                "last_7d": {
                    "digital_sales_qty": int(r["dg_qty_7"] or 0),
                    "digital_revenue": float(r["dg_rev_7"] or 0.0),
                    "vinyl_sales_qty": int(r["vn_qty_7"] or 0),
                    "vinyl_revenue": float(r["vn_rev_7"] or 0.0),
                    "streams": int(r["st_cnt_7"] or 0),
                },
                "last_30d": {
                    "digital_sales_qty": int(r["dg_qty_30"] or 0),
                    "digital_revenue": float(r["dg_rev_30"] or 0.0),
                    "vinyl_sales_qty": int(r["vn_qty_30"] or 0),
                    "vinyl_revenue": float(r["vn_rev_30"] or 0.0),
                    "streams": int(r["st_cnt_30"] or 0),
                },
            }
