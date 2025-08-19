# File: backend/services/venue_availability.py
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

class VenueAvailabilityService:
    """
    Availability is derived from tour_stops with status in ('pending','confirmed').
    A venue is unavailable for any overlapping interval against existing stops that
    are not cancelled.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)
        self._ensure_min_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_min_schema(self) -> None:
        # defensive: ensure tables exist if migrations not yet run
        with self._conn() as conn:
            c = conn.cursor()
            c.execute("""
            CREATE TABLE IF NOT EXISTS venues (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT NOT NULL,
              city TEXT, country TEXT, capacity INTEGER,
              created_at TEXT DEFAULT (datetime('now'))
            )""")
            c.execute("""
            CREATE TABLE IF NOT EXISTS tours (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              band_id INTEGER NOT NULL,
              name TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'draft',
              created_at TEXT DEFAULT (datetime('now'))
            )""")
            c.execute("""
            CREATE TABLE IF NOT EXISTS tour_stops (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              tour_id INTEGER NOT NULL,
              venue_id INTEGER NOT NULL,
              date_start TEXT NOT NULL,
              date_end TEXT NOT NULL,
              order_index INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL DEFAULT 'pending',
              notes TEXT,
              created_at TEXT DEFAULT (datetime('now'))
            )""")

    @staticmethod
    def _overlap_sql() -> str:
        # Two ranges [a_start, a_end] and [b_start, b_end] overlap iff a_start <= b_end AND b_start <= a_end
        return ("""
            (date_start <= :end AND :start <= date_end)
        """)

    def is_available(self, venue_id: int, start: str, end: str, exclude_stop_id: Optional[int] = None) -> bool:
        """Return True if venue has no overlapping *active* stops in [start, end]."""
        with self._conn() as conn:
            c = conn.cursor()
            params = {"venue_id": venue_id, "start": start, "end": end}
            sql = f"""
                SELECT COUNT(*) AS cnt
                FROM tour_stops
                WHERE venue_id = :venue_id
                  AND status IN ('pending','confirmed')
                  AND {self._overlap_sql()}
            """
            if exclude_stop_id:
                sql += " AND id != :exclude_stop_id"
                params["exclude_stop_id"] = exclude_stop_id
            c.execute(sql, params)
            return int(c.fetchone()[0]) == 0

    def venue_conflicts(self, venue_id: int, start: str, end: str) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            c = conn.cursor()
            c.execute(f"""
                SELECT id, tour_id, date_start, date_end, status
                FROM tour_stops
                WHERE venue_id = :venue_id
                  AND status IN ('pending','confirmed')
                  AND {self._overlap_sql()}
                ORDER BY date_start
            """, {"venue_id": venue_id, "start": start, "end": end})
            return [dict(r) for r in c.fetchall()]

    def get_venue(self, venue_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, city, country, capacity FROM venues WHERE id=?", (venue_id,))
            row = c.fetchone()
            return dict(row) if row else None

    def availability_window(self, venue_id: int, start: str, end: str) -> Dict[str, Any]:
        """Returns availability boolean and any conflicting stops for quick UI display."""
        conflicts = self.venue_conflicts(venue_id, start, end)
        return {"venue_id": venue_id, "available": len(conflicts) == 0, "conflicts": conflicts}
