# File: backend/services/tour_service.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from utils.db import get_conn
from services.venue_availability import VenueAvailabilityService
from core.errors import AppError, VenueConflictError, TourMinStopsError
from services.achievement_service import AchievementService
from services.weather_service import WeatherService
from services.economy_service import EconomyService
from services.fame_service import FameService
from models.economy_config import get_config
from models.tour import Tour as TourModel, TourLeg, TicketTier, Expense

RECORDING_FAME_THRESHOLD = 1000
MAX_RECORDINGS_PER_YEAR = 5

class TourService:
    """Service handling both legacy DB backed operations and lightweight tour
    simulations used in tests.

    The existing methods (create_tour, add_stop, ...) remain untouched so that
    older tests continue to function.  New functionality for scheduling shows,
    computing travel logistics and simulating attendance operates purely on
    in-memory dataclasses defined in :mod:`models.tour`.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        achievements: Optional[AchievementService] = None,
        weather: Optional[WeatherService] = None,
        economy: Optional[EconomyService] = None,
        fame: Optional[FameService] = None,
    ):
        self.db_path = db_path
        self.availability = VenueAvailabilityService(self.db_path)
        self.achievements = achievements or AchievementService(self.db_path)
        self.weather = weather or WeatherService()
        self.economy = economy or EconomyService(self.db_path)
        self.fame = fame
        # Ensure economy tables exist for simulations
        try:
            self.economy.ensure_schema()
        except Exception:
            pass

        # in-memory storage for simulated tours
        self.tours: Dict[int, TourModel] = {}

    def _assert_recording_allowed(self, band_id: int, date_str: str) -> None:
        fame_total = self.fame.get_total_fame(band_id) if self.fame else 0
        if fame_total < RECORDING_FAME_THRESHOLD:
            raise AppError(
                "Band lacks required fame to record this stop.",
                code="FAME_TOO_LOW",
            )
        year = date_str.split("-")[0]
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                SELECT COUNT(*) FROM tour_stops ts
                JOIN tours t ON t.id = ts.tour_id
                WHERE t.band_id = ? AND ts.is_recorded = 1 AND substr(ts.date_start,1,4) = ?
                """,
                (band_id, year),
            )
            count = int(c.fetchone()[0] or 0)
        if count >= MAX_RECORDINGS_PER_YEAR:
            raise AppError(
                "Recording limit reached for this year.",
                code="RECORDING_LIMIT_REACHED",
            )

    # ---- Tours ----
    def create_tour(
        self,
        band_id: int,
        name: str,
        start_date: str = "",
        end_date: str = "",
        route: Optional[List[str]] = None,
        vehicle_type: str = "van",
    ) -> Dict[str, Any]:
        """Create a tour record.

        This preserves the original behaviour of inserting into the ``tours``
        table while also instantiating an in-memory :class:`Tour` model that is
        used by the simulation helpers defined later in this service.
        """

        if not name or not name.strip():
            raise AppError("Tour name is required.", code="TOUR_NAME_REQUIRED")
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO tours (band_id, name) VALUES (?, ?)", (band_id, name.strip()))
            tour_id = int(c.lastrowid)

        model = TourModel(
            id=tour_id,
            band_id=band_id,
            title=name.strip(),
            start_date=start_date,
            end_date=end_date,
            route=route or [],
            vehicle_type=vehicle_type,
        )
        self.tours[tour_id] = model

        return {"id": tour_id, "band_id": band_id, "name": name.strip(), "status": "draft"}

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
        tour = self.get_tour(tour_id)
        try:
            self.achievements.grant(tour["band_id"], "first_tour")
        except Exception:
            pass
        return tour

    # ---- Stops ----
    def add_stop(
        self,
        tour_id: int,
        venue_id: int,
        date_start: str,
        date_end: str,
        order_index: int,
        notes: str = "",
        is_recorded: bool = False,
    ) -> Dict[str, Any]:
        # Verify tour exists (raises if not)
        tour = self.get_tour(tour_id)

        if not date_start or not date_end:
            raise AppError("date_start and date_end are required.", code="STOP_DATES_REQUIRED")
        if date_end < date_start:
            raise AppError("date_end must be on/after date_start.", code="STOP_DATE_ORDER_INVALID")

        # Availability
        if not self.availability.is_available(venue_id=venue_id, start=date_start, end=date_end):
            conflicts = self.availability.venue_conflicts(venue_id, date_start, date_end)
            raise VenueConflictError(f"Venue not available in window; conflicts: {conflicts}")

        if is_recorded:
            self._assert_recording_allowed(tour["band_id"], date_start)
            self.economy.charge_recording_fee(tour["band_id"])

        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """INSERT INTO tour_stops (tour_id, venue_id, date_start, date_end, order_index, status, notes, is_recorded)
                       VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)""",
                (
                    tour_id,
                    venue_id,
                    date_start,
                    date_end,
                    order_index,
                    notes,
                    int(is_recorded),
                ),
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

    def update_stop_recording(self, stop_id: int, is_recorded: bool) -> Dict[str, Any]:
        """Toggle the recording flag for a tour stop.

        This verifies that the band is eligible to record the stop when
        setting ``is_recorded`` to ``True`` and then persists the change.
        """

        stop = self.get_stop(stop_id)
        tour = self.get_tour(stop["tour_id"])
        if is_recorded and not stop["is_recorded"]:
            self._assert_recording_allowed(tour["band_id"], stop["date_start"])
            self.economy.charge_recording_fee(tour["band_id"])
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE tour_stops SET is_recorded=? WHERE id=?",
                (int(is_recorded), stop_id),
            )
        return self.get_stop(stop_id)

    def get_stop(self, stop_id: int) -> Dict[str, Any]:
        with get_conn(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """SELECT id, tour_id, venue_id, date_start, date_end, order_index, status, notes, is_recorded
                       FROM tour_stops WHERE id=?""",
                (stop_id,),
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
                """SELECT id, tour_id, venue_id, date_start, date_end, order_index, status, notes, is_recorded
                       FROM tour_stops WHERE tour_id=?
                       ORDER BY order_index ASC, date_start ASC""",
                (tour_id,),
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

    # ------------------------------------------------------------------
    # New simulation helpers
    # ------------------------------------------------------------------

    def schedule_show(
        self,
        tour_id: int,
        city: str,
        venue: str,
        date: str,
        ticket_tiers: Optional[List[TicketTier]] = None,
        expenses: Optional[List[Expense]] = None,
        is_recorded: bool = False,
    ) -> Dict[str, Any]:
        tour = self.tours.get(tour_id)
        if not tour:
            raise AppError("Tour not found.", code="TOUR_NOT_FOUND")
        if is_recorded:
            self._assert_recording_allowed(tour.band_id, date)
        leg = TourLeg(
            city=city,
            venue=venue,
            date=date,
            ticket_tiers=ticket_tiers or [],
            expenses=expenses or [],
            is_recorded=is_recorded,
        )
        if tour.legs:
            prev_city = tour.legs[-1].city
            leg.travel_distance = self._estimate_distance(prev_city, city)
            leg.travel_hours = round(leg.travel_distance / 60.0, 2)
        tour.legs.append(leg)
        tour.route.append(city)
        return leg.to_dict()

    def sell_tickets(
        self, tour_id: int, leg_index: int, tier_name: str, quantity: int
    ) -> Dict[str, Any]:
        tour = self.tours.get(tour_id)
        if not tour:
            raise AppError("Tour not found.", code="TOUR_NOT_FOUND")
        try:
            leg = tour.legs[leg_index]
        except IndexError:
            raise AppError("Invalid leg index.", code="LEG_NOT_FOUND")
        tier = next((t for t in leg.ticket_tiers if t.name == tier_name), None)
        if not tier:
            raise AppError("Ticket tier not found.", code="TIER_NOT_FOUND")
        available = max(tier.capacity - tier.sold, 0)
        qty = min(quantity, available)
        tier.sold += qty
        return {"sold": tier.sold, "remaining": tier.capacity - tier.sold}

    def simulate_attendance(self, tour_id: int, leg_index: int) -> Dict[str, Any]:
        tour = self.tours.get(tour_id)
        if not tour:
            raise AppError("Tour not found.", code="TOUR_NOT_FOUND")
        try:
            leg = tour.legs[leg_index]
        except IndexError:
            raise AppError("Invalid leg index.", code="LEG_NOT_FOUND")

        forecast = self.weather.get_forecast(leg.city)
        sold = sum(t.sold for t in leg.ticket_tiers)
        attendance = sold
        status = "completed"
        if getattr(forecast, "event", None) and getattr(forecast.event, "type", "") == "storm":
            attendance = 0
            status = "cancelled"
        elif forecast.condition == "rain":
            attendance = int(sold * 0.7)
        leg.attendance = attendance
        leg.status = status

        payout_cents = get_config().payout_rate
        revenue = attendance * payout_cents / 100.0
        leg.revenue = revenue
        total_expenses = sum(e.amount for e in leg.expenses)
        leg.profit = revenue - total_expenses
        if leg.profit > 0:
            # deposit profit in cents
            try:
                self.economy.deposit(tour.band_id, int(leg.profit * 100))
            except Exception:
                pass
        return leg.to_dict()

    def report(self, tour_id: int) -> Dict[str, Any]:
        tour = self.tours.get(tour_id)
        if not tour:
            raise AppError("Tour not found.", code="TOUR_NOT_FOUND")
        totals = {
            "attendance": sum(l.attendance for l in tour.legs),
            "revenue": sum(l.revenue for l in tour.legs),
            "profit": sum(l.profit for l in tour.legs),
        }
        return {"tour": tour.to_dict(), "totals": totals}

    # ---- util ----
    @staticmethod
    def _estimate_distance(a: str, b: str) -> float:
        """Very rough distance estimator used for tests."""
        return abs(len(a) - len(b)) * 50 + 100


# Alias retained for compatibility with older imports
TourError = AppError
