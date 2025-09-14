import os
import sys
import tempfile
from pathlib import Path

import httpx
import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

from services.economy_service import EconomyService
from services.payment_service import (
    PaymentError,
    PaymentService,
    PayPalGateway,
    StripeAPIGateway,
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


def setup_stripe_service(monkeypatch, post_resp: httpx.Response, get_resp: httpx.Response):
    fd, path = tempfile.mkstemp()
    os.close(fd)
    econ = EconomyService(db_path=path)
    econ.ensure_schema()
    monkeypatch.setenv("STRIPE_API_KEY", "test")
    monkeypatch.setattr(httpx, "post", lambda *a, **k: post_resp)
    monkeypatch.setattr(httpx, "get", lambda *a, **k: get_resp)
    gateway = StripeAPIGateway()
    svc = PaymentService(gateway, econ)
    return svc


def test_stripe_api_success(monkeypatch):
    post_resp = httpx.Response(200, json={"id": "pi_test"}, request=httpx.Request("POST", "http://test"))
    get_resp = httpx.Response(200, json={"status": "succeeded"}, request=httpx.Request("GET", "http://test"))
    svc = setup_stripe_service(monkeypatch, post_resp, get_resp)
    pid = svc.initiate_purchase(user_id=1, amount_cents=500)
    svc.verify_callback(pid)
    assert svc.economy_service.get_balance(1) == 500


def test_stripe_api_failure(monkeypatch):
    post_resp = httpx.Response(200, json={"id": "pi_test"}, request=httpx.Request("POST", "http://test"))
    get_resp = httpx.Response(200, json={"status": "requires_payment_method"}, request=httpx.Request("GET", "http://test"))
    svc = setup_stripe_service(monkeypatch, post_resp, get_resp)
    pid = svc.initiate_purchase(user_id=1, amount_cents=500)
    with pytest.raises(PaymentError):
        svc.verify_callback(pid)
    assert svc.economy_service.get_balance(1) == 0


def test_stripe_api_missing_key(monkeypatch):
    monkeypatch.delenv("STRIPE_API_KEY", raising=False)
    with pytest.raises(PaymentError):
        StripeAPIGateway()
