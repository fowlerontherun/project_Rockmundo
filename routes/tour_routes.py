"""API routes for tour simulation."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
try:  # Pydantic may be stubbed in tests
    from pydantic import Field
except Exception:  # pragma: no cover - fallback for minimal pydantic
    def Field(default=None, **kwargs):  # type: ignore
        return default
from typing import Any, List

from services.tour_service import TourService, TourError
from models.tour import TicketTier, Expense
from services.weather_service import WeatherService
from services.economy_service import EconomyService
from services.tour_logistics_service import TourLogisticsService
from services.transport_service import TransportService

router = APIRouter(prefix="/tours", tags=["Tours"])

# Initialise service with simple weather and economy modules
_economy = EconomyService()
try:
    _economy.ensure_schema()
except Exception:
    pass
svc = TourService(weather=WeatherService(), economy=_economy)
_logistics = TourLogisticsService(db=None, transport=TransportService(db=None))


# ----------------------- Pydantic models -----------------------
class CreateTourIn(BaseModel):
    band_id: int = Field(..., ge=1)
    title: str
    start_date: str = ""
    end_date: str = ""
    route: List[str] = []
    vehicle_type: str = "van"


class TicketTierIn(BaseModel):
    name: str
    price: float
    capacity: int


class ExpenseIn(BaseModel):
    description: str
    amount: float


class ScheduleShowIn(BaseModel):
    tour_id: int
    city: str
    venue: str
    date: str
    ticket_tiers: List[TicketTierIn] = []
    expenses: List[ExpenseIn] = []


class SellTicketsIn(BaseModel):
    tour_id: int
    leg_index: int
    tier_name: str
    quantity: int


class SimulateIn(BaseModel):
    tour_id: int
    leg_index: int


class TravelDisruptionIn(BaseModel):
    vehicle_type: str = "van"
    origin: str
    destination: str
    weather: str = "clear"


# ----------------------- Routes -----------------------
@router.post("/")
def create_tour(payload: CreateTourIn):
    info = svc.create_tour(
        band_id=payload.band_id,
        name=payload.title,
        start_date=payload.start_date,
        end_date=payload.end_date,
        route=payload.route,
        vehicle_type=payload.vehicle_type,
    )
    return svc.tours[info["id"]].to_dict()


@router.post("/schedule")
def schedule_show(payload: ScheduleShowIn):
    tiers = [TicketTier(**(t.dict() if hasattr(t, "dict") else t)) for t in payload.ticket_tiers]
    expenses = [Expense(**(e.dict() if hasattr(e, "dict") else e)) for e in payload.expenses]
    try:
        return svc.schedule_show(payload.tour_id, payload.city, payload.venue, payload.date, tiers, expenses)
    except TourError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/sell")
def sell_tickets(payload: SellTicketsIn):
    try:
        return svc.sell_tickets(payload.tour_id, payload.leg_index, payload.tier_name, payload.quantity)
    except TourError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/simulate")
def simulate(payload: SimulateIn):
    try:
        return svc.simulate_attendance(payload.tour_id, payload.leg_index)
    except TourError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/travel/disruptions")
def travel_disruptions(payload: TravelDisruptionIn):
    return _logistics.check_disruptions(
        payload.vehicle_type,
        payload.origin,
        payload.destination,
        weather=payload.weather,
    )


@router.get("/{tour_id}/report")
def report(tour_id: int):
    try:
        return svc.report(tour_id)
    except TourError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ----------------------- Simple planner API -----------------------
# These endpoints back the lightweight tour planner UI.  Data is stored in
# memory for demonstration/testing purposes only and is not persisted.
_planner_schedule: dict[str, Any] = {}
_planner_dates: list[dict] = []
_planner_expenses: list[dict] = []


@router.get("/planner/schedule")
def planner_get_schedule():
    return _planner_schedule


@router.put("/planner/schedule/{time}")
def planner_save_slot(time: str, payload: dict):
    _planner_schedule[time] = payload.get("value")
    return {"time": time, "value": _planner_schedule[time]}


@router.delete("/planner/schedule/{time}")
def planner_delete_slot(time: str):
    _planner_schedule.pop(time, None)
    return {"status": "ok"}


@router.post("/planner/schedule")
def planner_add_date(item: dict):
    _planner_dates.append(item)
    return {"schedule": _planner_dates}


@router.delete("/planner/schedule")
def planner_delete_date(item: dict):
    try:
        _planner_dates.remove(item)
    except ValueError:
        pass
    return {"schedule": _planner_dates}


@router.post("/planner/expenses")
def planner_add_expense(item: dict):
    _planner_expenses.append(item)
    return {"expenses": _planner_expenses}


@router.delete("/planner/expenses")
def planner_delete_expense(item: dict):
    try:
        _planner_expenses.remove(item)
    except ValueError:
        pass
    return {"expenses": _planner_expenses}
