import logging
import sys
from pathlib import Path

import pytest

# Make backend modules like `models` importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from services.construction_service import ConstructionService
from models.construction import BuildPhase, Blueprint, ConstructionTask


class DummyEconomy:
    def __init__(self) -> None:
        self.schema_ensured = False
        self.deposits: list[tuple[int, int]] = []
        self.withdrawals: list[tuple[int, int]] = []

    def ensure_schema(self) -> None:  # pragma: no cover - simple tracking
        self.schema_ensured = True

    def deposit(self, owner_id: int, amount: int) -> None:  # pragma: no cover - simple tracking
        self.deposits.append((owner_id, amount))

    def withdraw(self, owner_id: int, amount: int) -> None:  # pragma: no cover - simple tracking
        self.withdrawals.append((owner_id, amount))


class StubPropertyService:
    db_path = ":memory:"

    def __init__(self) -> None:
        self.schema_ensured = False
        self.upgrade_calls: list[tuple[int, int]] = []

    def ensure_schema(self) -> None:  # pragma: no cover - simple tracking
        self.schema_ensured = True

    def upgrade_property(self, property_id: int, owner_id: int) -> None:  # pragma: no cover - simple tracking
        self.upgrade_calls.append((property_id, owner_id))


class FailingPropertySchemaService(StubPropertyService):
    def ensure_schema(self) -> None:
        super().ensure_schema()
        raise RuntimeError("prop schema fail")


class FailingUpgradePropertyService(StubPropertyService):
    def upgrade_property(self, property_id: int, owner_id: int) -> None:
        super().upgrade_property(property_id, owner_id)
        raise RuntimeError("upgrade fail")


class StubVenueService:
    def __init__(self) -> None:
        self.schema_ensured = False
        self.update_calls: list[tuple[int, dict]] = []

    def ensure_schema(self) -> None:  # pragma: no cover - simple tracking
        self.schema_ensured = True

    def update_venue(self, venue_id: int, updates: dict) -> None:  # pragma: no cover - simple tracking
        self.update_calls.append((venue_id, updates))

    def get_venue(self, venue_id: int) -> dict:  # pragma: no cover - simple stub
        return {}


class FailingVenueSchemaService(StubVenueService):
    def ensure_schema(self) -> None:
        super().ensure_schema()
        raise RuntimeError("venue schema fail")


class FailingUpdateVenueService(StubVenueService):
    def update_venue(self, venue_id: int, updates: dict) -> None:
        super().update_venue(venue_id, updates)
        raise RuntimeError("update fail")


def _make_service(prop_service: StubPropertyService, venue_service: StubVenueService) -> ConstructionService:
    economy = DummyEconomy()
    return ConstructionService(economy=economy, properties=prop_service, venues=venue_service)


def test_init_fails_when_property_schema_fails(caplog: pytest.LogCaptureFixture) -> None:
    venue_service = StubVenueService()
    prop_service = FailingPropertySchemaService()
    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError, match="prop schema fail"):
            _make_service(prop_service, venue_service)
    assert prop_service.schema_ensured is True
    assert "Failed to ensure property schema" in caplog.text


def test_init_fails_when_venue_schema_fails(caplog: pytest.LogCaptureFixture) -> None:
    prop_service = StubPropertyService()
    venue_service = FailingVenueSchemaService()
    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError, match="venue schema fail"):
            _make_service(prop_service, venue_service)
    assert venue_service.schema_ensured is True
    assert "Failed to ensure venue schema" in caplog.text


def test_complete_task_logs_property_upgrade_failure(caplog: pytest.LogCaptureFixture) -> None:
    prop_service = FailingUpgradePropertyService()
    venue_service = StubVenueService()
    service = _make_service(prop_service, venue_service)
    blueprint = Blueprint("bp", 0, [BuildPhase("phase", 1)], "property", {})
    task = ConstructionTask(parcel_id=1, blueprint=blueprint, owner_id=1, target_id=1)
    service.queue.append(task)
    with caplog.at_level(logging.ERROR):
        service.advance_time(1)
    assert "Failed to upgrade property" in caplog.text
    assert prop_service.upgrade_calls == [(1, 1)]
    assert service.economy.deposits == [(1, 0)]
    assert service.queue == []


def test_complete_task_logs_venue_update_failure(caplog: pytest.LogCaptureFixture) -> None:
    prop_service = StubPropertyService()
    venue_service = FailingUpdateVenueService()
    service = _make_service(prop_service, venue_service)
    blueprint = Blueprint("bp", 0, [BuildPhase("phase", 1)], "venue", {})
    task = ConstructionTask(parcel_id=1, blueprint=blueprint, owner_id=1, target_id=1)
    service.queue.append(task)
    with caplog.at_level(logging.ERROR):
        service.advance_time(1)
    assert "Failed to update venue" in caplog.text
    assert venue_service.update_calls == [(1, {})]
    assert service.queue == []
