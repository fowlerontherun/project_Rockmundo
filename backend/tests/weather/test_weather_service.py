import os
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from backend.models.weather import ClimateZone, Forecast, WeatherEvent
from backend.services import event_service
from backend.services.economy_service import EconomyService
from backend.services.property_service import PropertyService
from backend.services.weather_service import WeatherService, weather_service


def test_forecast_generates_event(monkeypatch):
    svc = WeatherService()
    svc.add_zone(ClimateZone(name="north", pattern="temperate", avg_high=20, avg_low=10))
    monkeypatch.setattr("backend.services.weather_service.random.random", lambda: 0.05)
    monkeypatch.setattr("backend.services.weather_service.random.randint", lambda a, b: a)
    forecast = svc.get_forecast("north")
    assert forecast.event and forecast.event.type == "storm"


def test_adjust_event_attendance(monkeypatch):
    def fake_forecast(region: str) -> Forecast:
        return Forecast(region=region, date=date.today(), condition="sunny", high=20, low=10,
                        event=WeatherEvent(type="storm", severity=5))

    monkeypatch.setattr(event_service.weather_service, "get_forecast", fake_forecast)
    assert event_service.adjust_event_attendance(100, "north") == 70


def test_rent_adjusted_by_weather(monkeypatch):
    fd, path = tempfile.mkstemp()
    os.close(fd)
    econ = EconomyService(db_path=path)
    econ.ensure_schema()
    svc = PropertyService(db_path=path, economy=econ, weather=weather_service)
    svc.ensure_schema()
    econ.deposit(1, 100000)
    svc.buy_property(1, "Flat", "apt", "north", 50000, 1000)

    def fake_forecast(region: str) -> Forecast:
        return Forecast(region=region, date=date.today(), condition="sunny", high=20, low=10,
                        event=WeatherEvent(type="storm", severity=7))

    monkeypatch.setattr(weather_service, "get_forecast", fake_forecast)
    total = svc.collect_rent(1)
    assert total == 500  # 50% due to storm
    assert econ.get_balance(1) == 100000 - 50000 + 500
