"""SQLAlchemy models for core economy tables.

These lightweight ORM mappings are used by the economy service for
accounting operations.  They intentionally contain only the fields required
for the tests in this kata.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.ext.declarative import declarative_base


# A local ``Base`` is used so that the tables can be created on demand in the
# tests without interfering with the vast number of other models in the
# project.
Base = declarative_base()


class Account(Base):
    """Represents a user's currency account."""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    balance_cents = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Transaction(Base):
    """Record of money moving between accounts or external sources."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # deposit, withdrawal, transfer
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, nullable=False)
    src_account_id = Column(Integer, ForeignKey("accounts.id"))
    dest_account_id = Column(Integer, ForeignKey("accounts.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LedgerEntry(Base):
    """Account-level delta for a transaction."""

    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    transaction_id = Column(
        Integer, ForeignKey("transactions.id"), nullable=False
    )
    delta_cents = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

