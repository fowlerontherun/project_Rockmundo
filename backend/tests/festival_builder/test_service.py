import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

from services.festival_builder_service import (
    BookingConflictError,
    FestivalBuilderService,
    FestivalError,
)


def setup_service():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    svc = FestivalBuilderService(db_path=path)
    return svc


def test_creation():
    svc = setup_service()
    fid = svc.create_festival(
        name="TestFest",
        owner_id=1,
        stages={"Main": 2},
        ticket_tiers=[{"name": "GA", "price_cents": 1000, "capacity": 100}],
        sponsors=[{"name": "Acme", "contribution_cents": 50000}],
    )
    fest = svc.get_festival(fid)
    assert fest.name == "TestFest"
    assert "Main" in fest.stages
    assert fest.ticket_tiers[0].name == "GA"


def test_booking_conflict():
    svc = setup_service()
    fid = svc.create_festival(
        "Fest",
        owner_id=1,
        stages={"Stage": 1},
        ticket_tiers=[{"name": "GA", "price_cents": 1000, "capacity": 10}],
    )
    svc.book_act(fid, "Stage", 0, band_id=2, payout_cents=500)
    with pytest.raises(BookingConflictError):
        svc.book_act(fid, "Stage", 0, band_id=3, payout_cents=500)


def test_financial_reconciliation():
    svc = setup_service()
    fid = svc.create_festival(
        "Fest",
        owner_id=1,
        stages={"Stage": 1},
        ticket_tiers=[{"name": "GA", "price_cents": 1500, "capacity": 10}],
        sponsors=[{"name": "Acme", "contribution_cents": 5000}],
    )
    svc.sell_tickets(fid, "GA", 2, buyer_id=5)
    svc.book_act(fid, "Stage", 0, band_id=2, payout_cents=500)
    finances = svc.get_finances(fid)
    assert finances["revenue"] == 3000
    assert finances["payouts"] == 500
    assert svc.economy.get_balance(1) == 3000
    assert svc.economy.get_balance(2) == 500
    fest = svc.get_festival(fid)
    assert fest.sponsors[0].name == "Acme"


def test_proposals_and_voting():
    svc = setup_service()
    pid = svc.propose_festival(proposer_id=1, name="IdeaFest")
    assert pid == 1
    proposals = svc.list_proposals()
    assert proposals[0].name == "IdeaFest"
    votes = svc.vote_on_proposal(pid, voter_id=2)
    assert votes == 1
    with pytest.raises(FestivalError):
        svc.vote_on_proposal(pid, voter_id=2)
