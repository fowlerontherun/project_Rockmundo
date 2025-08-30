from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Loan:
    """Represents a loan issued to a user."""

    id: Optional[int]
    user_id: int
    principal_cents: int
    balance_cents: int
    interest_rate: float
    term_days: int
    created_at: Optional[datetime] = None


@dataclass
class InterestAccount:
    """An interest bearing account linked to a user."""

    id: Optional[int]
    user_id: int
    balance_cents: int
    interest_rate: float
    currency: str = "USD"
    created_at: Optional[datetime] = None


@dataclass
class ExchangeRate:
    """Exchange rate between two currencies."""

    base_currency: str
    target_currency: str
    rate: float
    updated_at: Optional[datetime] = None
