import sqlite3
from datetime import datetime

import sqlite3
from datetime import datetime

from backend.services.city_service import city_service
from backend.services import event_service, live_performance_service
from backend.services.quest_service import QuestService
from backend.models.weather import Forecast
from backend.models.city import City


def setup_function(_):
    city_service.cities.clear()


def test_daily_update_changes_market_index(monkeypatch):
    city_service.add_city(City(name="Metro", population=1_000_000, style_preferences={"rock": 1.0}))
    monkeypatch.setattr("backend.services.city_service.random.uniform", lambda a, b: 0.05)
    city_service.update_daily()
    city = city_service.get_city("Metro")
    assert city and city.market_index > 1.0


def test_city_adjusts_event_attendance(monkeypatch):
    city_service.add_city(City(name="Metro", population=1_000_000, style_preferences={}, event_modifier=1.2))

    def fake_forecast(region: str) -> Forecast:
        return Forecast(region=region, date=datetime.utcnow(), condition="sunny", high=20, low=10, event=None)

    monkeypatch.setattr(event_service.weather_service, "get_forecast", fake_forecast)
    attendance = event_service.adjust_event_attendance(100, "Metro")
    assert attendance == 120


def test_city_trends_affect_merch_sales(monkeypatch):
    city_service.add_city(City(name="Metro", population=1_000_000, style_preferences={}, event_modifier=1.5, market_index=2.0))

    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE bands (id INTEGER PRIMARY KEY, fame INTEGER, skill REAL, revenue INTEGER)")
    cur.execute("CREATE TABLE live_performances (band_id INTEGER, city TEXT, venue TEXT, date TEXT, setlist TEXT, crowd_size INTEGER, fame_earned INTEGER, revenue_earned INTEGER, skill_gain REAL, merch_sold INTEGER)")
    cur.execute("INSERT INTO bands (id, fame, skill, revenue) VALUES (1, 100, 0, 0)")

    monkeypatch.setattr(live_performance_service, "DB_PATH", ":memory:")
    monkeypatch.setattr(live_performance_service.sqlite3, "connect", lambda _: conn)
    monkeypatch.setattr(live_performance_service.random, "randint", lambda a, b: a)

    result = live_performance_service.simulate_gig(1, "Metro", "The Spot", ["song"])
    assert result["crowd_size"] == 300  # 200 base * 1.5 modifier
    assert result["merch_sold"] == 90   # 300 * 0.15 * 2.0


def test_city_influences_quest_generation():
    city_service.add_city(City(name="Metro", population=500_000, style_preferences={"rock": 2.0, "pop": 0.5}))
    svc = QuestService()
    quest = svc.generate_city_quest("Metro")
    assert "rock" in quest.name.lower()
    assert "rock" in quest.stages["start"].description.lower()
