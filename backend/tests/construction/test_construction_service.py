import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

from backend.services.construction_service import ConstructionService
from backend.services.economy_service import EconomyService
from backend.services.property_service import PropertyService
from backend.services.venue_service import VenueService
from backend.models.construction import Blueprint, BuildPhase


@pytest.fixture
def setup_services():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    econ = EconomyService(db_path=path)
    econ.ensure_schema()
    prop = PropertyService(db_path=path, economy=econ)
    prop.ensure_schema()
    venue = VenueService(db_path=path, economy=econ)
    venue.ensure_schema()
    svc = ConstructionService(economy=econ, properties=prop, venues=venue)
    return svc, prop, venue, econ


def test_build_queue_and_property_upgrade(setup_services):
    svc, prop_service, _, econ = setup_services
    owner = 1
    econ.deposit(owner, 50000)
    # purchase land and property
    parcel_id = svc.purchase_land(owner, "NYC", 100, 1000)
    pid = prop_service.buy_property(owner, "Studio", "studio", "NYC", 10000, 1000)
    # blueprint to upgrade property
    blueprint = Blueprint(
        name="Studio Upgrade",
        cost=10000,
        phases=[BuildPhase("foundation", 2), BuildPhase("finishing", 1)],
        target_type="property",
        upgrade_effect={"base_rent": 100},
    )
    svc.submit_design(parcel_id, blueprint, owner, pid)
    assert len(svc.get_queue()) == 1
    svc.advance_time(3)
    assert svc.get_queue() == []
    prop = prop_service.list_properties(owner)[0]
    assert prop["level"] == 2
    assert prop["base_rent"] == 1100
    assert econ.get_balance(owner) == 50000 - 1000 - 10000 - 10000


def test_venue_upgrade(setup_services):
    svc, _, venue_service, econ = setup_services
    owner = 2
    econ.deposit(owner, 5000)
    venue = venue_service.create_venue(owner, "Hall", "City", "Country", 500, 1000)
    parcel_id = svc.purchase_land(owner, "City", 50, 0)
    blueprint = Blueprint(
        name="Expand Hall",
        cost=500,
        phases=[BuildPhase("work", 1)],
        target_type="venue",
        upgrade_effect={"capacity": 100},
    )
    svc.submit_design(parcel_id, blueprint, owner, venue["id"])
    svc.advance_time(1)
    updated = venue_service.get_venue(venue["id"])
    assert updated["capacity"] == 600
    assert econ.get_balance(owner) == 5000 - 1000 - 500
