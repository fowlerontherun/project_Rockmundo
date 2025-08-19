# File: backend/services/tour_service.py
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

from services.venue_availability import VenueAvailabilityService

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"

class TourError(Exception):
    pass

class TourService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)
        self.availability = VenueAvailabilityService(self.db_path)
        self._ensure_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
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

    # ---- Tours ----
    def create_tour(self, band_id: int, name: str) -> Dict[str, Any]:
        with self._conn() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO tours (band_id, name) VALUES (?, ?)", (band_id, name))
            return {"id": int(c.lastrowid), "band_id": band_id, "name": name, "status": "draft"}

    def get_tour(self, tour_id: int) -> Dict[str, Any]:
        with self._conn() as conn:
            c = conn.cursor()
            c.execute("SELECT id, band_id, name, status, created_at FROM tours WHERE id=?", (tour_id,))
            row = c.fetchone()
            if not row:
                raise TourError("Tour not found.")
            return dict(row)

    def list_tours(self, band_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            c = conn.cursor()
            cond, params = [], []
            if band_id is not None:
                cond.append("band_id=?"); params.append(band_id)
            if status is not None:
                cond.append("status=?"); params.append(status)
            where = (" WHERE " + " AND ".join(cond)) if cond else ""
            c.execute(f"SELECT id, band_id, name, status, created_at FROM tours{where} ORDER BY created_at DESC LIMIT ? OFFSET ?", (*params, limit, offset))
            return [dict(r) for r in c.fetchall()]

    def confirm_tour(self, tour_id: int) -> Dict[str, Any]:
        with self._conn() as conn:
            c = conn.cursor()
            # Verify there are at least two stops and none overlapping by venue
            c.execute("SELECT COUNT(*) FROM tour_stops WHERE tour_id=? AND status != 'cancelled'", (tour_id,))
            if int(c.fetchone()[0]) < 2:
                raise TourError("A tour must have at least 2 active stops before confirmation.")
            c.execute("UPDATE tours SET status='confirmed' WHERE id=?", (tour_id,))
            return self.get_tour(tour_id)

    # ---- Stops ----
    def add_stop(self, tour_id: int, venue_id: int, date_start: str, date_end: str, order_index: int, notes: str = "") -> Dict[str, Any]:
        # Verify tour exists
        self.get_tour(tour_id)

        # Availability
        if not self.availability.is_available(venue_id=venue_id, start=date_start, end=date_end):
            conflicts = self.availability.venue_conflicts(venue_id, date_start, date_end)
            raise TourError(f"Venue not available in window; conflicts: {conflicts}")

        with self._conn() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO tour_stops (tour_id, venue_id, date_start, date_end, order_index, status, notes)
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
            """, (tour_id, venue_id, date_start, date_end, order_index, notes))
            stop_id = int(c.lastrowid)
            return self.get_stop(stop_id)

    def update_stop_status(self, stop_id: int, status: str) -> Dict[str, Any]:
        if status not in ("pending","confirmed","cancelled"):
            raise TourError("Invalid stop status.")
        with self._conn() as conn:
            c = conn.cursor()
            c.execute("UPDATE tour_stops SET status=? WHERE id=?", (status, stop_id))
        return self.get_stop(stop_id)

    def get_stop(self, stop_id: int) -> Dict[str, Any]:
        with self._conn() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, tour_id, venue_id, date_start, date_end, order_index, status, notes
                FROM tour_stops WHERE id=?
            """, (stop_id,))
            row = c.fetchone()
            if not row:
                raise TourError("Stop not found.")
            return dict(row)

    def list_stops(self, tour_id: int) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, tour_id, venue_id, date_start, date_end, order_index, status, notes
                FROM tour_stops WHERE tour_id=?
                ORDER BY order_index ASC, date_start ASC
            """, (tour_id,))
            return [dict(r) for r in c.fetchall()]

    # ---- Venue helpers passthrough ----
    def venue_availability(self, venue_id: int, start: str, end: str) -> Dict[str, Any]:
        return self.availability.availability_window(venue_id, start, end)

    def create_venue(self, name: str, city: str = "", country: str = "", capacity: int = 0) -> Dict[str, Any]:
        with self._conn() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO venues (name, city, country, capacity) VALUES (?, ?, ?, ?)",
                      (name, city, country, capacity))
            vid = int(c.lastrowid)
            return {"id": vid, "name": name, "city": city, "country": country, "capacity": capacity}

    def list_venues(self, q: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            c = conn.cursor()
            if q:
                c.execute("SELECT id, name, city, country, capacity FROM venues WHERE name LIKE ? ORDER BY name LIMIT ? OFFSET ?",
                          (f"%{q}%", limit, offset))
            else:
                c.execute("SELECT id, name, city, country, capacity FROM venues ORDER BY name LIMIT ? OFFSET ?",
                          (limit, offset))
            return [dict(r) for r in c.fetchall()]
