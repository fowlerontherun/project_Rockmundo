"""Service for handling purchases and subscriptions via a payment gateway."""

from __future__ import annotations

import os

import httpx
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import uuid4
from abc import ABC, abstractmethod

from backend.models.payment import PremiumCurrency, PurchaseRecord, SubscriptionPlan
from backend.services.economy_service import EconomyService


class PaymentError(Exception):
    """Raised when a payment operation fails."""


@dataclass
class PaymentGateway(ABC):
    """Minimal gateway interface used for testing.
    """Abstract payment gateway definition.
    Concrete subclasses integrate with providers like Stripe or PayPal and
    must implement the methods below.
    """

    @abstractmethod
    def create_payment(self, amount_cents: int, currency: str) -> str:
        """Create a payment request and return its provider identifier."""

    @abstractmethod
    def verify_payment(self, payment_id: str) -> bool:
        """Return ``True`` if the payment completed successfully."""
        """Create a remote payment and return its provider identifier."""

    @abstractmethod
    def verify_payment(self, payment_id: str) -> bool:
        """Return ``True`` if the payment succeeded on the provider side."""

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
    api_key: str = field(default_factory=lambda: os.getenv("STRIPE_API_KEY", ""))
    webhook_secret: Optional[str] = field(
        default_factory=lambda: os.getenv("STRIPE_WEBHOOK_SECRET")
    )

    def __post_init__(self) -> None:
        if not self.api_key:
            raise PaymentError("Stripe API key not configured")

    def create_payment(self, amount_cents: int, currency: str) -> str:
        data = {
            "amount": amount_cents,
            "currency": currency,
            "payment_method_types[]": "card",
        }
        try:
            resp = httpx.post(
                f"{self.base_url}/payment_intents", data=data, auth=(self.api_key, "")
            )
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network errors
            raise PaymentError(f"Stripe create_payment failed: {exc}") from exc
        try:
            return resp.json()["id"]
        except KeyError as exc:
            raise PaymentError("Stripe response missing id") from exc

    def verify_payment(self, payment_id: str) -> bool:
        try:
            resp = httpx.get(
                f"{self.base_url}/payment_intents/{payment_id}", auth=(self.api_key, "")
            )
            resp.raise_for_status()
        except Exception as exc:  # pragma: no cover - network errors
            raise PaymentError(f"Stripe verify_payment failed: {exc}") from exc
        return resp.json().get("status") == "succeeded"


class PaymentService:
    """Main entry point for handling payment operations."""

    def __init__(
        self,
        gateway: PaymentGateway,
        economy_service: EconomyService,
        premium_currency: Optional[PremiumCurrency] = None,
    ) -> None:
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
