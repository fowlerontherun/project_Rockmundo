import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

from backend.services.economy_service import EconomyService
from backend.services.legal_service import LegalService
from backend.services.karma_service import KarmaService


class InMemoryKarmaDB:
    def __init__(self):
        self.totals = {}
        self.events = []

    def insert_karma_event(self, event):
        self.events.append(event)

    def update_user_karma(self, user_id, amount):
        self.totals[user_id] = self.totals.get(user_id, 0) + amount

    def get_user_karma_total(self, user_id):
        return self.totals.get(user_id, 0)


def setup_services():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    economy = EconomyService(db_path=path)
    economy.ensure_schema()
    karma_db = InMemoryKarmaDB()
    karma = KarmaService(karma_db)
    legal = LegalService(economy, karma)
    return legal, economy, karma


def test_case_lifecycle():
    legal, economy, karma = setup_services()
    economy.deposit(2, 1000)
    case = legal.create_case(1, 2, "Unpaid performance", 500)
    legal.add_filing(case.id, 2, "Will pay soon")
    legal.arbitrate_case(case.id, "guilty", 500)
    stored = legal.get_case(case.id)
    assert stored.status == "closed"
    assert economy.get_balance(1) == 500
    assert economy.get_balance(2) == 500
    assert karma.get_user_karma(2) < 0
