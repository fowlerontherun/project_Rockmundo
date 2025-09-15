import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure project root on path
sys.path.append(str(Path(__file__).resolve().parents[3]))

import pydantic
if not hasattr(pydantic, "Field"):
    def Field(default=None, **kwargs):  # type: ignore
        return default
    pydantic.Field = Field  # type: ignore

import types

core_errors = types.ModuleType("core.errors")


class AppError(Exception):
    pass


class VenueConflictError(AppError):
    pass


class TourMinStopsError(AppError):
    pass


core_errors.AppError = AppError
core_errors.VenueConflictError = VenueConflictError
core_errors.TourMinStopsError = TourMinStopsError
sys.modules["core.errors"] = core_errors

from routes.tour_routes import router
from backend.services.tour_service import TourService
from backend.services.weather_service import WeatherService
from backend.services.economy_service import EconomyService
from backend.models.tour import TicketTier, Expense
from backend.models.economy_config import set_config, EconomyConfig
import importlib
alt_economy = importlib.import_module("models.economy_config")
from backend.models.weather import Forecast, WeatherEvent


@pytest.fixture
def svc(tmp_path):
    db = tmp_path / "econ.db"
    econ = EconomyService(db)
    econ.ensure_schema()
    weather = WeatherService()
    service = TourService(db_path=db, weather=weather, economy=econ)
    return service, weather, econ


def set_payout(rate):
    cfg = EconomyConfig(payout_rate=rate)
    set_config(cfg)
    alt_economy.set_config(alt_economy.EconomyConfig(payout_rate=rate))


def _sunny(region, for_date=None):
    return Forecast(region=region, date=for_date, condition="sunny", high=25, low=15, event=None)


def _storm(region, for_date=None):
    return Forecast(region=region, date=for_date, condition="rain", high=10, low=5, event=WeatherEvent(type="storm", severity=9))


def test_successful_show(svc):
    service, weather, _ = svc
    weather.get_forecast = _sunny
    info = service.create_tour(1, "Mini", start_date="2024", end_date="2024")
    service.schedule_show(info["id"], "NYC", "Hall", "2024-01-01", [TicketTier("GA", 10.0, 100)], [Expense("rent", 100)])
    service.sell_tickets(info["id"], 0, "GA", 50)
    result = service.simulate_attendance(info["id"], 0)
    assert result["attendance"] == 50
    assert result["status"] == "completed"


def test_cancelled_show(svc):
    service, weather, _ = svc
    weather.get_forecast = _storm
    info = service.create_tour(1, "Mini", start_date="2024", end_date="2024")
    service.schedule_show(info["id"], "NYC", "Hall", "2024-01-01", [TicketTier("GA", 10.0, 100)], [])
    service.sell_tickets(info["id"], 0, "GA", 50)
    result = service.simulate_attendance(info["id"], 0)
    assert result["attendance"] == 0
    assert result["status"] == "cancelled"


def test_profit_calculation(svc):
    service, weather, econ = svc
    weather.get_forecast = _sunny
    set_payout(500)
    info = service.create_tour(1, "Mini", start_date="2024", end_date="2024")
    service.schedule_show(info["id"], "NYC", "Hall", "2024-01-01", [TicketTier("GA", 10.0, 100)], [Expense("rent", 100)])
    service.sell_tickets(info["id"], 0, "GA", 50)
    leg = service.simulate_attendance(info["id"], 0)
    assert pytest.approx(150.0, rel=1e-3) == leg["profit"]
    report = service.report(info["id"])
    assert report["totals"]["profit"] == leg["profit"]
    assert econ.get_balance(1) == 15000


def test_routes(tmp_path):
    """Basic smoke test invoking the route handlers directly."""
    set_payout(100)
    from routes import tour_routes as tr

    info = tr.create_tour(tr.CreateTourIn(band_id=1, title="RouteTour", start_date="2024", end_date="2024"))
    tid = info["id"]
    tr.schedule_show(
        tr.ScheduleShowIn(
            tour_id=tid,
            city="NYC",
            venue="Hall",
            date="2024-01-01",
            ticket_tiers=[{"name": "GA", "price": 10.0, "capacity": 100}],
            expenses=[],
        )
    )
    tr.sell_tickets(tr.SellTicketsIn(tour_id=tid, leg_index=0, tier_name="GA", quantity=10))
    tr.simulate(tr.SimulateIn(tour_id=tid, leg_index=0))
    rep = tr.report(tid)
    assert rep["tour"]["id"] == tid
