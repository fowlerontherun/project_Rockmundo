import sys
from pathlib import Path

import httpx
import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

from services.economy_service import EconomyService
from services.payment_service import (
    PaymentError,
    PaymentService,
    StripeAPIGateway,
)


def setup_service(monkeypatch, tmp_path, success: bool):
    """Create a PaymentService using the real Stripe API gateway.

    HTTP requests are mocked via monkeypatch to avoid network calls.
    """

    db_path = tmp_path / "test.db"
    econ = EconomyService(str(db_path))
    econ.ensure_schema()

    monkeypatch.setenv("STRIPE_API_KEY", "sk_test")

    def fake_post(url, data=None, auth=None):
        assert auth == ("sk_test", "")
        assert url == "https://api.stripe.com/v1/payment_intents"
        return httpx.Response(
            200, json={"id": "pi_test"}, request=httpx.Request("POST", url)
        )

    def fake_get(url, auth=None):
        assert auth == ("sk_test", "")
        assert url == "https://api.stripe.com/v1/payment_intents/pi_test"
        status = "succeeded" if success else "requires_payment_method"
        return httpx.Response(
            200,
            json={"id": "pi_test", "status": status},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(httpx, "get", fake_get)

    gateway = StripeAPIGateway()
    svc = PaymentService(gateway, econ)
    return svc, econ


def test_purchase_success(monkeypatch, tmp_path):
    svc, econ = setup_service(monkeypatch, tmp_path, True)
    pid = svc.initiate_purchase(user_id=1, amount_cents=500)
    svc.verify_callback(pid)
    assert econ.get_balance(1) == 500


def test_purchase_failure(monkeypatch, tmp_path):
    svc, econ = setup_service(monkeypatch, tmp_path, False)
    pid = svc.initiate_purchase(user_id=1, amount_cents=500)
    with pytest.raises(PaymentError):
        svc.verify_callback(pid)
    assert econ.get_balance(1) == 0

