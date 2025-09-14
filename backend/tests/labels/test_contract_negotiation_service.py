import os
import sys
import tempfile
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))

from models.label_management_models import NegotiationStage
from backend.services.contract_negotiation_service import ContractNegotiationService
from backend.services.economy_service import EconomyService


def setup_services():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    econ = EconomyService(db_path=path)
    econ.ensure_schema()
    svc = ContractNegotiationService(economy=econ, db_path=path)
    return econ, svc


def test_negotiation_flow_and_recoupment():
    economy, service = setup_services()
    # label has funds for advance and royalties
    economy.deposit(1, 5000)
    terms = {
        "advance_cents": 1000,
        "royalty_tiers": [{"threshold_units": 0, "rate": 0.1}],
        "term_months": 12,
        "territory": "US",
        "recoupable_budgets_cents": 500,
        "options": [],
        "obligations": [],
    }
    neg = service.create_offer(1, 2, terms)
    assert neg.stage == NegotiationStage.OFFER

    neg = service.counter_offer(neg.id, terms)
    assert neg.stage == NegotiationStage.COUNTER

    neg = service.accept_offer(neg.id)
    assert neg.stage == NegotiationStage.ACCEPTED
    assert neg.recoupable_cents == 1500

    # deposit revenue for royalty payout
    economy.deposit(1, 1000)
    neg = service.apply_royalty_payment(neg.id, 700)
    assert neg.recouped_cents == 700
