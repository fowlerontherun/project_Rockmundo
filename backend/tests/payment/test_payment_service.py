import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

from backend.services.economy_service import EconomyService
from backend.services.payment_service import (
    PaymentError,
    PaymentService,
    PayPalGateway,
    StripeGateway,
)


def setup_service(success: bool, gateway_cls):
    fd, path = tempfile.mkstemp()
    os.close(fd)
    econ = EconomyService(db_path=path)
    econ.ensure_schema()
    gateway = gateway_cls(succeed=success)
    svc = PaymentService(gateway, econ)
    return svc


@pytest.mark.parametrize("gateway_cls", [StripeGateway, PayPalGateway])
def test_purchase_success(gateway_cls):
    svc = setup_service(True, gateway_cls)
    pid = svc.initiate_purchase(user_id=1, amount_cents=500)
    svc.verify_callback(pid)
    assert svc.economy_service.get_balance(1) == 500


@pytest.mark.parametrize("gateway_cls", [StripeGateway, PayPalGateway])
def test_purchase_failure(gateway_cls):
    svc = setup_service(False, gateway_cls)
    pid = svc.initiate_purchase(user_id=1, amount_cents=500)
    with pytest.raises(PaymentError):
        svc.verify_callback(pid)
    assert svc.economy_service.get_balance(1) == 0
