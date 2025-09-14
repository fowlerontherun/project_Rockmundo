import os
import sys
import tempfile
from pathlib import Path
import types

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

# Stub out missing core.errors dependencies before importing TourService
core_errors = types.ModuleType("core.errors")
class AppError(Exception):
    pass
class VenueConflictError(Exception):
    pass
class TourMinStopsError(Exception):
    pass
core_errors.AppError = AppError
core_errors.VenueConflictError = VenueConflictError
core_errors.TourMinStopsError = TourMinStopsError
sys.modules.setdefault("core.errors", core_errors)

# Provide utils.db expected by tour_service
import sqlite3
utils_pkg = types.ModuleType("utils")
db_module = types.ModuleType("utils.db")
def get_conn(path: str):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
db_module.get_conn = get_conn
utils_pkg.db = db_module
sys.modules["utils"] = utils_pkg
sys.modules["utils.db"] = db_module

from services.economy_service import EconomyService
from services.tour_service import TourService
from services.weather_service import WeatherService
from backend.economy.models import Account, LedgerEntry


class DummyFameService:
    def get_total_fame(self, band_id: int) -> int:
        return 10_000


class DummyAchievements:
    def grant(self, user_id: int, code: str) -> None:
        pass


def setup_services():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    econ = EconomyService(db_path=path)
    econ.ensure_schema()
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS bands (id INTEGER PRIMARY KEY, recorded_shows_year INTEGER DEFAULT 0)"
        )
        cur.execute("INSERT INTO bands (id, recorded_shows_year) VALUES (1,0)")
        conn.commit()
    tour = TourService(
        db_path=path,
        achievements=DummyAchievements(),
        weather=WeatherService(),
        economy=econ,
        fame=DummyFameService(),
    )
    return econ, tour


def test_recording_five_shows_deducts_total_cost():
    econ, tour = setup_services()
    band_id = 1
    initial = econ.recording_cost * 5
    econ.deposit(band_id, initial)
    tour_info = tour.create_tour(band_id, "Test Tour")
    stop_ids = []
    for i in range(5):
        stop = tour.add_stop(
            tour_id=tour_info["id"],
            venue_id=1,
            date_start=f"2025-01-0{i+1}",
            date_end=f"2025-01-0{i+1}",
            order_index=i,
        )
        stop_ids.append(stop["id"])
    for sid in stop_ids:
        tour.update_stop_recording(sid, True)
    assert econ.get_balance(band_id) == 0

    engine = create_engine(f"sqlite:///{econ.db_path}")
    with Session(engine) as session:
        acct_id = session.execute(
            select(Account.id).where(Account.user_id == band_id)
        ).scalar_one()
        entries = (
            session.execute(
                select(LedgerEntry)
                .where(LedgerEntry.account_id == acct_id)
                .order_by(LedgerEntry.id)
            )
            .scalars()
            .all()
        )
        assert [e.delta_cents for e in entries] == [initial] + [
            -econ.recording_cost
        ] * 5
