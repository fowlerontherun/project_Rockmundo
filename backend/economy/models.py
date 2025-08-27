from dataclasses import dataclass
from datetime import datetime


@dataclass
class Account:
    """Represents a user's currency account."""

    id: int
    user_id: int
    currency: str
    balance_cents: int
    created_at: datetime


@dataclass
class Transaction:
    """Record of money moving between accounts or external sources."""

    id: int
    type: str  # deposit, withdrawal, transfer
    amount_cents: int
    currency: str
    src_account_id: int | None
    dest_account_id: int | None
    created_at: datetime


@dataclass
class LedgerEntry:
    """Account-level delta for a transaction."""

    id: int
    account_id: int
    transaction_id: int
    delta_cents: int
    balance_after: int
    created_at: datetime
