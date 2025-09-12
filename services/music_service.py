# File: backend/services/music_service.py
from typing import Optional, Dict, Any
from utils.db import get_conn

class MusicService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def record_sale(self, item_id: int, quantity: int, revenue: float, is_vinyl: bool = False, meta: Optional[str] = None) -> Dict[str, Any]:
        event_type = "sale_vinyl" if is_vinyl else "sale_digital"
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO music_events (event_type, item_id, quantity, revenue, meta)
                VALUES (?, ?, ?, ?, ?)
            """, (event_type, item_id, quantity, revenue, meta))
            return {"id": int(cur.lastrowid), "event_type": event_type}

    def record_stream(self, item_id: int, count: int, meta: Optional[str] = None) -> Dict[str, Any]:
        with get_conn(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO music_events (event_type, item_id, quantity, revenue, meta)
                VALUES ('stream', ?, ?, 0.0, ?)
            """, (item_id, count, meta))
            return {"id": int(cur.lastrowid), "event_type": "stream"}
