import os
import sys
import tempfile
from pathlib import Path

import pytest
sys.path.append(str(Path(__file__).resolve().parents[3]))

from backend.services.contract_negotiation_service import ContractNegotiationService
from backend.services.economy_service import EconomyService
from backend.routes import contract_routes
from models.label_management_models import NegotiationStage


def setup_service():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    econ = EconomyService(db_path=path)
    econ.ensure_schema()
    svc = ContractNegotiationService(economy=econ)
    return svc, econ


def test_offer_counter_accept_flow():
    svc, econ = setup_service()
    econ.deposit(1, 10000)
    offer = svc.create_offer(1, 2, {"advance_cents": 4000, "royalty_rate": 0.1})
    assert offer.stage == NegotiationStage.OFFER
    offer = svc.counter_offer(offer.id, {"advance_cents": 3000, "royalty_rate": 0.2})
    assert offer.stage == NegotiationStage.COUNTER
    offer = svc.accept_offer(offer.id)
    assert offer.stage == NegotiationStage.ACCEPTED
    assert econ.get_balance(1) == 7000
    assert econ.get_balance(2) == 3000
    txns = econ.list_transactions(2)
    assert any(t.type == "royalty" for t in txns)


def test_accept_invalid():
    svc, _ = setup_service()
    with pytest.raises(ValueError):
        svc.accept_offer(999)


def test_cannot_accept_twice():
    svc, econ = setup_service()
    econ.deposit(1, 5000)
    offer = svc.create_offer(1, 2, {"advance_cents": 1000, "royalty_rate": 0.1})
    svc.accept_offer(offer.id)
    with pytest.raises(ValueError):
        svc.accept_offer(offer.id)


def test_route_flow(tmp_path):
    db = tmp_path / "test.db"
    economy = EconomyService(str(db))
    economy.ensure_schema()
    contract_routes.svc = ContractNegotiationService(economy)
    economy.deposit(1, 10000)
    offer = contract_routes.create_offer(contract_routes.OfferIn(label_id=1, band_id=2, terms={"advance_cents": 1000, "royalty_rate": 0.1}))
    nid = offer["id"]
    contract_routes.counter_offer(nid, contract_routes.CounterIn(terms={"advance_cents": 800, "royalty_rate": 0.15}))
    contract_routes.accept_offer(nid)
    assert economy.get_balance(2) == 800
