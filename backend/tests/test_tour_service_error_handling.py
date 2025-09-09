import sqlite3
import sys
import types

import pytest

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

from backend.services.economy_service import EconomyService  # noqa: E402
from backend.services.tour_service import TourService  # noqa: E402


class BoomEconomy(EconomyService):
    def ensure_schema(self) -> None:  # pragma: no cover - behaviour tested
        raise sqlite3.OperationalError("boom")


class ExplodingEconomy(EconomyService):
    def ensure_schema(self) -> None:  # pragma: no cover - behaviour tested
        raise RuntimeError("boom")


class FailingAchievements:
    def grant(self, user_id: int, code: str) -> None:  # pragma: no cover - simple stub
        raise ValueError("nope")


def test_init_logs_economy_schema_error(tmp_path, caplog):
    db = tmp_path / "test.db"
    econ = BoomEconomy(db)
    with caplog.at_level("ERROR"):
        TourService(db_path=str(db), economy=econ)
    assert "Economy schema setup failed" in caplog.text


def test_init_reraises_unexpected_error(tmp_path):
    db = tmp_path / "test.db"
    econ = ExplodingEconomy(db)
    with pytest.raises(RuntimeError):
        TourService(db_path=str(db), economy=econ)


def test_confirm_tour_logs_achievement_failure(tmp_path, caplog):
    db = tmp_path / "test.db"
    econ = EconomyService(db)
    failing = FailingAchievements()
    import backend.services.tour_service as ts

    ts.get_conn = lambda path: sqlite3.connect(path)
    svc = TourService(db_path=str(db), economy=econ, achievements=failing)
    venue = svc.create_venue("Club")
    tour = svc.create_tour(1, "Road Trip")
    svc.add_stop(tour["id"], venue["id"], "2024-01-01", "2024-01-02", 0)
    svc.add_stop(tour["id"], venue["id"], "2024-01-03", "2024-01-04", 1)
    with caplog.at_level("ERROR"):
        result = svc.confirm_tour(tour["id"])
    assert result["status"] == "confirmed"
    assert "Failed to grant tour achievement" in caplog.text

