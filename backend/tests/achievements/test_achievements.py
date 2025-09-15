import sqlite3
import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

import pydantic

from backend.services.achievement_service import AchievementService
from backend.services.economy_service import EconomyService
from backend.services.property_service import PropertyService

if not hasattr(pydantic, "Field"):
    def Field(default=None, **kwargs):
        return default
    pydantic.Field = Field

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

from routes import achievement_routes  # noqa: E402
from backend.services.chart_service import calculate_weekly_chart  # noqa: E402
from backend.services.tour_service import TourService  # noqa: E402


def setup_db(tmp_path):
    db = tmp_path / "test.db"
    return str(db)


def test_property_unlock(tmp_path):
    db = setup_db(tmp_path)
    ach = AchievementService(db)
    econ = EconomyService(db)
    econ.ensure_schema()
    svc = PropertyService(db_path=db, economy=econ, achievements=ach)
    svc.ensure_schema()
    econ.deposit(1, 100000)
    svc.buy_property(1, "Studio", "studio", "NYC", 50000, 1000)
    progress = ach.get_user_achievements(1)
    assert any(p["code"] == "first_property" and p["unlocked_at"] for p in progress)


def test_tour_unlock(tmp_path):
    db = setup_db(tmp_path)
    ach = AchievementService(db)
    svc = TourService(db_path=db, achievements=ach)
    tour = svc.create_tour(1, "Road Trip")
    v = svc.create_venue("Club")
    svc.add_stop(tour["id"], v["id"], "2024-01-01", "2024-01-02", 0)
    svc.add_stop(tour["id"], v["id"], "2024-01-03", "2024-01-04", 1)
    svc.confirm_tour(tour["id"])
    progress = ach.get_user_achievements(1)
    assert any(p["code"] == "first_tour" and p["unlocked_at"] for p in progress)


def test_chart_topper_unlock(tmp_path):
    db = setup_db(tmp_path)
    ach = AchievementService(db)
    # patch chart_service globals
    from backend.services import chart_service
    chart_service.DB_PATH = db
    chart_service.achievement_service = ach

    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE bands (id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE songs (id INTEGER PRIMARY KEY, title TEXT, band_id INTEGER);
            CREATE TABLE streams (id INTEGER PRIMARY KEY AUTOINCREMENT, song_id INTEGER, timestamp TEXT);
            CREATE TABLE earnings (id INTEGER PRIMARY KEY AUTOINCREMENT, source_type TEXT, source_id INTEGER, amount REAL, timestamp TEXT);
            CREATE TABLE chart_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, chart_type TEXT, region TEXT, week_start TEXT, position INTEGER, song_id INTEGER, band_name TEXT, score REAL, generated_at TEXT);
            """
        )
        cur.execute("INSERT INTO bands (id, name) VALUES (1, 'Band A')")
        cur.execute("INSERT INTO songs (id, title, band_id) VALUES (1, 'Hit', 1)")
        cur.execute("INSERT INTO streams (song_id, timestamp) VALUES (1, datetime('now'))")
        conn.commit()

    calculate_weekly_chart(start_date="2024-01-01")
    progress = ach.get_user_achievements(1)
    assert any(p["code"] == "chart_topper" and p["unlocked_at"] for p in progress)


def test_routes(tmp_path):
    db = setup_db(tmp_path)
    ach = AchievementService(db)
    achievement_routes.svc = ach

    ach.grant(1, "first_property")

    all_achs = achievement_routes.list_achievements()
    assert any(a["code"] == "first_property" for a in all_achs)

    data = achievement_routes.user_achievements(1)
    assert any(a["code"] == "first_property" and a["unlocked_at"] for a in data)

