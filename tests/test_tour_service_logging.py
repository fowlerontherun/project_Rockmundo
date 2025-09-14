import logging
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import backend.services as backend_services
sys.modules.setdefault("services", backend_services)

import backend.core as backend_core
sys.modules.setdefault("core", backend_core)

import backend.core.errors as core_errors
sys.modules.setdefault("core.errors", core_errors)



class AppError(Exception):
    pass


class VenueConflictError(AppError):
    pass


class TourMinStopsError(AppError):
    pass


core_errors.AppError = AppError
core_errors.VenueConflictError = VenueConflictError
core_errors.TourMinStopsError = TourMinStopsError

import backend.models as backend_models
sys.modules.setdefault("models", backend_models)

import backend.services.tour_service as tour_service_module
from services.tour_service import TourService


class DummyEconomy:
    def ensure_schema(self):
        pass


def setup_db(path):
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE tours (id INTEGER PRIMARY KEY, band_id INTEGER, name TEXT, status TEXT DEFAULT 'draft', created_at TEXT)"
    )
    conn.execute(
        "CREATE TABLE tour_stops (id INTEGER PRIMARY KEY, tour_id INTEGER, status TEXT)"
    )
    conn.execute(
        "INSERT INTO tours (id, band_id, name, status) VALUES (1, 1, 't', 'draft')"
    )
    conn.execute("INSERT INTO tour_stops (tour_id, status) VALUES (1, 'pending')")
    conn.execute("INSERT INTO tour_stops (tour_id, status) VALUES (1, 'pending')")
    conn.commit()
    conn.close()


def test_init_logs_and_raises(monkeypatch, caplog, tmp_path):
    class BadEconomy(DummyEconomy):
        def ensure_schema(self):
            raise RuntimeError("boom")

    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError):
            TourService(db_path=None, economy=BadEconomy())

    assert "Failed to ensure economy schema" in caplog.text


def test_confirm_tour_logs_achievement_failure(monkeypatch, caplog, tmp_path):
    db = tmp_path / "tour.db"
    setup_db(db)
    monkeypatch.setattr(tour_service_module, "get_conn", sqlite3.connect)

    class BadAchievement:
        def grant(self, *args, **kwargs):
            raise AppError("nope")

    svc = TourService(
        db_path=str(db),
        achievements=BadAchievement(),
        economy=DummyEconomy(),
    )

    with caplog.at_level(logging.WARNING):
        tour = svc.confirm_tour(1)
    assert tour["status"] == "confirmed"
    assert "Failed to grant achievement" in caplog.text


def test_confirm_tour_reraises_unexpected(monkeypatch, tmp_path):
    db = tmp_path / "tour2.db"
    setup_db(db)
    monkeypatch.setattr(tour_service_module, "get_conn", sqlite3.connect)

    class BoomAchievement:
        def grant(self, *args, **kwargs):
            raise RuntimeError("boom")

    svc = TourService(
        db_path=str(db),
        achievements=BoomAchievement(),
        economy=DummyEconomy(),
    )

    with pytest.raises(RuntimeError):
        svc.confirm_tour(1)

