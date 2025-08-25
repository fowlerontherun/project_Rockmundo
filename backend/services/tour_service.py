# File: backend/services/tour_service.py
from typing import List, Dict, Any, Optional
from utils.db import get_conn
from services.venue_availability import VenueAvailabilityService
from core.errors import AppError, VenueConflictError, TourMinStopsError

class TourService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.availability = VenueAvailabilityService(self.db_path)

    # ---- Tours ----
    def create_tour(self, band_id: int, name: str) -> Dict[str, Any]:
        if not name or not name.strip():
            raise AppError("Tour name is required.", code="TOUR_NAME_REQUIRED")
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO tours (band_id, name) VALUES (?, ?)", (band_id, name.strip()))
            return {"id": int(c.lastrowid), "band_id": band_id, "name": name.strip(), "status": "draft"}

    def get_tour(self, tour_id: int) -> Dict[str, Any]:
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT id, band_id, name, status, created_at FROM tours WHERE id=?", (tour_id,))
            row = c.fetchone()
            if not row:
                raise AppError("Tour not found.", code="TOUR_NOT_FOUND")
            cols = [d[0] for d in c.description]
            return dict(zip(cols, row))

    def list_tours(self, band_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            cond, params = [], []
            if band_id is not None:
                cond.append("band_id=?"); params.append(band_id)
            if status is not None:
                cond.append("status=?"); params.append(status)
            where = (" WHERE " + " AND ".join(cond)) if cond else ""
            c.execute(f"SELECT id, band_id, name, status, created_at FROM tours{where} ORDER BY created_at DESC LIMIT ? OFFSET ?", (*params, limit, offset))
            cols = [d[0] for d in c.description]
            return [dict(zip(cols, r)) for r in c.fetchall()]

    def confirm_tour(self, tour_id: int) -> Dict[str, Any]:
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM tour_stops WHERE tour_id=? AND status != 'cancelled'", (tour_id,))
            if int(c.fetchone()[0]) < 2:
                raise TourMinStopsError("A tour must have at least 2 active stops before confirmation.")
            c.execute("UPDATE tours SET status='confirmed' WHERE id=?", (tour_id,))
        return self.get_tour(tour_id)

    # ---- Stops ----
    def add_stop(self, tour_id: int, venue_id: int, date_start: str, date_end: str, order_index: int, notes: str = "") -> Dict[str, Any]:
        # Verify tour exists (raises if not)
        self.get_tour(tour_id)

        if not date_start or not date_end:
            raise AppError("date_start and date_end are required.", code="STOP_DATES_REQUIRED")
        if date_end < date_start:
            raise AppError("date_end must be on/after date_start.", code="STOP_DATE_ORDER_INVALID")

        # Availability
        if not self.availability.is_available(venue_id=venue_id, start=date_start, end=date_end):
            conflicts = self.availability.venue_conflicts(venue_id, date_start, date_end)
            raise VenueConflictError(f"Venue not available in window; conflicts: {conflicts}")

        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """INSERT INTO tour_stops (tour_id, venue_id, date_start, date_end, order_index, status, notes)
                       VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
                (tour_id, venue_id, date_start, date_end, order_index, notes),
            )
            stop_id = int(c.lastrowid)
        return self.get_stop(stop_id)

    def update_stop_status(self, stop_id: int, status: str) -> Dict[str, Any]:
        if status not in ("pending","confirmed","cancelled"):
            raise AppError("Invalid stop status.", code="STOP_STATUS_INVALID")
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute("UPDATE tour_stops SET status=? WHERE id=?", (status, stop_id))
        return self.get_stop(stop_id)

    def get_stop(self, stop_id: int) -> Dict[str, Any]:
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """SELECT id, tour_id, venue_id, date_start, date_end, order_index, status, notes
                       FROM tour_stops WHERE id=?""", (stop_id,)
            )
            row = c.fetchone()
            if not row:
                raise AppError("Stop not found.", code="STOP_NOT_FOUND")
            cols = [d[0] for d in c.description]
            return dict(zip(cols, row))

    def list_stops(self, tour_id: int) -> List[Dict[str, Any]]:
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """SELECT id, tour_id, venue_id, date_start, date_end, order_index, status, notes
                       FROM tour_stops WHERE tour_id=?
                       ORDER BY order_index ASC, date_start ASC""", (tour_id,)
            )
            cols = [d[0] for d in c.description]
            return [dict(zip(cols, r)) for r in c.fetchall()]

    # ---- Venue helpers passthrough ----
    def venue_availability(self, venue_id: int, start: str, end: str) -> Dict[str, Any]:
        return self.availability.availability_window(venue_id, start, end)

    def create_venue(self, name: str, city: str = "", country: str = "", capacity: int = 0) -> Dict[str, Any]:
        if not name or not name.strip():
            raise AppError("Venue name is required.", code="VENUE_NAME_REQUIRED")
        if capacity < 0:
            raise AppError("Capacity must be >= 0.", code="VENUE_CAPACITY_INVALID")
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO venues (name, city, country, capacity) VALUES (?, ?, ?, ?)", (name.strip(), city, country, capacity))
            vid = int(c.lastrowid)
            return {"id": vid, "name": name.strip(), "city": city, "country": country, "capacity": capacity}

    def list_venues(self, q: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            if q:
                c.execute("SELECT id, name, city, country, capacity FROM venues WHERE name LIKE ? ORDER BY name LIMIT ? OFFSET ?",
                          (f"%{q}%", limit, offset))
            else:
                c.execute("SELECT id, name, city, country, capacity FROM venues ORDER BY name LIMIT ? OFFSET ?",
                          (limit, offset))
            cols = [d[0] for d in c.description]
            return [dict(zip(cols, r)) for r in c.fetchall()]
