import logging
import sys
from pathlib import Path

import pytest

# Make backend modules like `models` importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT), str(ROOT / "backend")])

from services.construction_service import ConstructionService
from models.construction import BuildPhase, Blueprint, ConstructionTask


class DummyEconomy:
    def ensure_schema(self) -> None:  # pragma: no cover - no logic
        pass

    def deposit(self, owner_id: int, amount: int) -> None:  # pragma: no cover - no logic
        pass

    def withdraw(self, owner_id: int, amount: int) -> None:  # pragma: no cover - no logic
        pass


class StubPropertyService:
    db_path = ":memory:"

    def ensure_schema(self) -> None:  # pragma: no cover - no logic
        pass

    def upgrade_property(self, property_id: int, owner_id: int) -> None:  # pragma: no cover - no logic
        pass


class FailingPropertySchemaService(StubPropertyService):
    def ensure_schema(self) -> None:
        raise RuntimeError("prop schema fail")


class FailingUpgradePropertyService(StubPropertyService):
    def upgrade_property(self, property_id: int, owner_id: int) -> None:
        raise RuntimeError("upgrade fail")


class StubVenueService:
    def ensure_schema(self) -> None:  # pragma: no cover - no logic
        pass

    def update_venue(self, venue_id: int, updates: dict) -> None:  # pragma: no cover - no logic
        pass

    def get_venue(self, venue_id: int) -> dict:  # pragma: no cover - no logic
        return {}


class FailingVenueSchemaService(StubVenueService):
    def ensure_schema(self) -> None:
        raise RuntimeError("venue schema fail")


class FailingUpdateVenueService(StubVenueService):
    def update_venue(self, venue_id: int, updates: dict) -> None:
        raise RuntimeError("update fail")


def _make_service(prop_service: StubPropertyService, venue_service: StubVenueService) -> ConstructionService:
    economy = DummyEconomy()
    return ConstructionService(economy=economy, properties=prop_service, venues=venue_service)


def test_init_fails_when_property_schema_fails(caplog: pytest.LogCaptureFixture) -> None:
    venue_service = StubVenueService()
    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError, match="prop schema fail"):
            _make_service(FailingPropertySchemaService(), venue_service)
    assert "Failed to ensure property schema" in caplog.text


def test_init_fails_when_venue_schema_fails(caplog: pytest.LogCaptureFixture) -> None:
    prop_service = StubPropertyService()
    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError, match="venue schema fail"):
            _make_service(prop_service, FailingVenueSchemaService())
    assert "Failed to ensure venue schema" in caplog.text


def test_complete_task_logs_property_upgrade_failure(caplog: pytest.LogCaptureFixture) -> None:
    service = _make_service(FailingUpgradePropertyService(), StubVenueService())
    blueprint = Blueprint("bp", 0, [BuildPhase("phase", 1)], "property", {})
    task = ConstructionTask(parcel_id=1, blueprint=blueprint, owner_id=1, target_id=1)
    with caplog.at_level(logging.ERROR):
        service._complete_task(task)
    assert "Failed to upgrade property" in caplog.text


def test_complete_task_logs_venue_update_failure(caplog: pytest.LogCaptureFixture) -> None:
    service = _make_service(StubPropertyService(), FailingUpdateVenueService())
    blueprint = Blueprint("bp", 0, [BuildPhase("phase", 1)], "venue", {})
    task = ConstructionTask(parcel_id=1, blueprint=blueprint, owner_id=1, target_id=1)
    with caplog.at_level(logging.ERROR):
        service._complete_task(task)
    assert "Failed to update venue" in caplog.text
