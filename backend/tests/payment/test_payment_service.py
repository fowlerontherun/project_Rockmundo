import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

from backend.services.economy_service import EconomyService
from backend.services.payment_service import PaymentError, PaymentGateway, PaymentService


class DummyGateway(PaymentGateway):
    def __init__(self, succeed: bool = True):
        self.succeed = succeed
        self.counter = 0

    def create_payment(self, amount_cents: int, currency: str) -> str:
        self.counter += 1
        return f"pay_{self.counter}"

    def verify_payment(self, payment_id: str) -> bool:
        return self.succeed


def setup_service(success: bool):
    fd, path = tempfile.mkstemp()
    os.close(fd)
    econ = EconomyService(db_path=path)
    econ.ensure_schema()
    gateway = DummyGateway(succeed=success)
    svc = PaymentService(gateway, econ)
    return svc


def test_purchase_success():
    svc = setup_service(True)
    pid = svc.initiate_purchase(user_id=1, amount_cents=500)
    svc.verify_callback(pid)
    assert svc.economy_service.get_balance(1) == 500


def test_purchase_failure():
    svc = setup_service(False)
    pid = svc.initiate_purchase(user_id=1, amount_cents=500)
    with pytest.raises(PaymentError):
        svc.verify_callback(pid)
    assert svc.economy_service.get_balance(1) == 0
