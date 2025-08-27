import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

from backend.services.property_service import PropertyService
from backend.services.economy_service import EconomyService


class DummyFameService:
    def __init__(self):
        self.calls = []

    def award_fame(self, band_id, source, amount, reason):
        self.calls.append((band_id, source, amount, reason))


def setup_service():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    econ = EconomyService(db_path=path)
    econ.ensure_schema()
    fame = DummyFameService()
    svc = PropertyService(db_path=path, economy=econ, fame=fame)
    svc.ensure_schema()
    return svc, econ, fame


def test_purchase_and_list():
    svc, econ, fame = setup_service()
    econ.deposit(1, 100000)
    pid = svc.buy_property(1, "Studio", "studio", "NYC", 50000, 1000)
    props = svc.list_properties(1)
    assert len(props) == 1 and props[0]["id"] == pid
    assert econ.get_balance(1) == 50000


def test_upgrade_calls_fame():
    svc, econ, fame = setup_service()
    econ.deposit(1, 200000)
    pid = svc.buy_property(1, "Studio", "studio", "NYC", 50000, 1000)
    prop = svc.upgrade_property(pid, 1)
    assert prop["level"] == 2
    assert fame.calls


def test_sell_property():
    svc, econ, fame = setup_service()
    econ.deposit(1, 100000)
    pid = svc.buy_property(1, "Studio", "studio", "NYC", 50000, 1000)
    sale = svc.sell_property(pid, 1)
    assert sale == int(50000 * 0.8)
    assert svc.list_properties(1) == []
    assert econ.get_balance(1) == 100000 - 50000 + int(50000 * 0.8)
