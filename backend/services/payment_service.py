"""Service for handling purchases and subscriptions via a payment gateway."""

from __future__ import annotations

import os

import httpx
from dataclasses import dataclass, field
from typing import Dict, Optional, Type
from uuid import uuid4

from backend.models.payment import PremiumCurrency, PurchaseRecord, SubscriptionPlan
from backend.services.economy_service import EconomyService


class PaymentError(Exception):
    """Raised when a payment operation fails."""


@dataclass
class PaymentGateway:
    """Minimal gateway interface used for testing.

    Real implementations would integrate with providers like Stripe or PayPal.
    """

    def create_payment(self, amount_cents: int, currency: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def verify_payment(self, payment_id: str) -> bool:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class MockGateway(PaymentGateway):
    """In-memory gateway useful for tests.

    It simulates an external provider by recording expected outcomes for
    generated payment identifiers.
    """

    prefix: str
    succeed: bool = True
    counter: int = 0
    payments: Dict[str, bool] = field(default_factory=dict)

    def create_payment(self, amount_cents: int, currency: str) -> str:
        self.counter += 1
        payment_id = f"{self.prefix}_{uuid4().hex}_{self.counter}"
        # store expected result for verification
        self.payments[payment_id] = self.succeed
        return payment_id

    def verify_payment(self, payment_id: str) -> bool:
        return self.payments.get(payment_id, False)


class StripeGateway(MockGateway):
    """Mock Stripe integration used for testing payment flows."""

    def __init__(self, succeed: bool = True):
        super().__init__(prefix="stripe", succeed=succeed)


class PayPalGateway(MockGateway):
    """Mock PayPal integration used for testing payment flows."""

    def __init__(self, succeed: bool = True):
        super().__init__(prefix="paypal", succeed=succeed)


@dataclass
class StripeAPIGateway(PaymentGateway):
    """Stripe payment gateway using real HTTP API calls.

    API credentials are read from environment variables:

    ``STRIPE_API_KEY`` – secret API key used for authenticating requests.
    ``STRIPE_WEBHOOK_SECRET`` – optional secret for webhook verification.
    """

    base_url: str = "https://api.stripe.com/v1"
    api_key: str = field(default_factory=lambda: os.environ["STRIPE_API_KEY"])
    webhook_secret: Optional[str] = field(
        default_factory=lambda: os.environ.get("STRIPE_WEBHOOK_SECRET")
    )

    def create_payment(self, amount_cents: int, currency: str) -> str:
        data = {
            "amount": amount_cents,
            "currency": currency,
            "payment_method_types[]": "card",
        }
        resp = httpx.post(
            f"{self.base_url}/payment_intents", data=data, auth=(self.api_key, "")
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def verify_payment(self, payment_id: str) -> bool:
        resp = httpx.get(
            f"{self.base_url}/payment_intents/{payment_id}", auth=(self.api_key, "")
        )
        resp.raise_for_status()
        return resp.json().get("status") == "succeeded"


class PaymentService:
    """Main entry point for handling payment operations."""

    # registry of available gateways for simple configuration
    gateway_registry: Dict[str, Type[PaymentGateway]] = {
        "stripe": StripeGateway,
        "paypal": PayPalGateway,
        "stripe_api": StripeAPIGateway,
    }

    def __init__(self, gateway: Optional[PaymentGateway], economy_service: EconomyService,
                 premium_currency: Optional[PremiumCurrency] = None, gateway_name: str = "stripe"):
        if gateway is None:
            gateway_cls = self.gateway_registry.get(gateway_name.lower())
            if not gateway_cls:
                raise ValueError(f"Unsupported gateway: {gateway_name}")
            gateway = gateway_cls()
        self.gateway = gateway
        self.economy_service = economy_service
        self.premium_currency = premium_currency or PremiumCurrency(
            code="COIN", name="Coins", exchange_rate=100
        )
        self.purchases: Dict[str, PurchaseRecord] = {}
        self.subscriptions: Dict[int, str] = {}  # user_id -> plan_id

    # -------- purchases --------
    def initiate_purchase(self, user_id: int, amount_cents: int, currency: str = "USD") -> str:
        payment_id = self.gateway.create_payment(amount_cents, currency)
        self.purchases[payment_id] = PurchaseRecord(
            id=payment_id,
            user_id=user_id,
            amount_cents=amount_cents,
            currency=currency,
            status="pending",
        )
        return payment_id

    def verify_callback(self, payment_id: str) -> PurchaseRecord:
        record = self.purchases.get(payment_id)
        if not record:
            raise PaymentError("Unknown payment")
        if not self.gateway.verify_payment(payment_id):
            record.status = "failed"
            raise PaymentError("Verification failed")
        record.status = "completed"
        # credit premium currency
        self.economy_service.credit_purchase(record.user_id, record.amount_cents,
                                             self.premium_currency)
        return record

    # -------- subscriptions --------
    def create_subscription(self, user_id: int, plan: SubscriptionPlan) -> None:
        self.subscriptions[user_id] = plan.id

    def cancel_subscription(self, user_id: int) -> None:
        self.subscriptions.pop(user_id, None)
