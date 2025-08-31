import sqlite3

from backend.services import live_performance_service
from backend.services.city_service import city_service
from backend.models.city import City


def test_simulate_gig_parses_structured_setlist(monkeypatch):
    city_service.cities.clear()
    city_service.add_city(City(name="Metro", population=1_000_000, style_preferences={}, event_modifier=1.0, market_index=1.0))

    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE bands (id INTEGER PRIMARY KEY, fame INTEGER, skill REAL, revenue INTEGER)")
    cur.execute(
        "CREATE TABLE live_performances (band_id INTEGER, city TEXT, venue TEXT, date TEXT, setlist TEXT, crowd_size INTEGER, fame_earned INTEGER, revenue_earned INTEGER, skill_gain REAL, merch_sold INTEGER)"
    )
    cur.execute("INSERT INTO bands (id, fame, skill, revenue) VALUES (1, 100, 0, 0)")

    monkeypatch.setattr(live_performance_service, "DB_PATH", ":memory:")
    monkeypatch.setattr(live_performance_service.sqlite3, "connect", lambda _: conn)
    monkeypatch.setattr(live_performance_service.random, "randint", lambda a, b: a)
    monkeypatch.setattr(live_performance_service.gear_service, "get_band_bonus", lambda band_id, name: 0)
    monkeypatch.setattr(live_performance_service, "is_skill_blocked", lambda band_id, skill_id: False)

    setlist = [
        {"type": "song", "reference": "1"},
        {"type": "activity", "description": "banter"},
        {"type": "song", "reference": "2", "encore": True},
    ]

    result = live_performance_service.simulate_gig(1, "Metro", "The Spot", setlist)

    assert result["fame_earned"] == 28
    assert result["skill_gain"] == 0.7

