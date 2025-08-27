"""Service for handling purchases and subscriptions via a payment gateway."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from backend.models.payment import PremiumCurrency, PurchaseRecord, SubscriptionPlan

from .economy_service import EconomyService


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


class PaymentService:
    def __init__(self, gateway: PaymentGateway, economy_service: EconomyService,
                 premium_currency: Optional[PremiumCurrency] = None):
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
