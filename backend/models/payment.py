from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class PurchaseRecord:
    """Record representing a real-money purchase."""

    id: str
    user_id: int
    amount_cents: int
    currency: str
    status: str  # pending, completed, failed
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SubscriptionPlan:
    """Represents a subscription plan offering premium features."""

    id: str
    name: str
    price_cents: int
    currency: str
    interval: str  # e.g. 'monthly', 'yearly'
    benefits: List[str] = field(default_factory=list)


@dataclass
class PremiumCurrency:
    """Describes a premium currency purchasable with real money."""

    code: str
    name: str
    exchange_rate: int  # number of premium units per 100 cents (1 USD)
