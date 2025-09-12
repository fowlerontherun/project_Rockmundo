from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from backend.services.xp_reward_service import xp_reward_service

from backend.models.banking import Loan
from backend.models.economy_config import get_config
from backend.utils.logging import get_logger

from sqlalchemy import create_engine, select, or_
from sqlalchemy.orm import Session, sessionmaker

from backend.economy.models import (
    Base,
    Account,
    Transaction as TransactionModel,
    LedgerEntry,
    RECORDING_COST,
)

logger = get_logger(__name__)

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class EconomyError(Exception):
    """Generic economy related failure."""


@dataclass
class TransactionRecord:
    id: int
    type: str
    amount_cents: int
    currency: str
    src_account_id: Optional[int]
    dest_account_id: Optional[int]
    created_at: str


class EconomyService:
    """Minimal economy service used in tests."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or DB_PATH)
        # SQLAlchemy engine/session for ORM-backed tables
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False, future=True)
        # Expose recording cost constant
        self.recording_cost = RECORDING_COST

    # ---------------- schema ----------------
    def ensure_schema(self) -> None:
        # Create ORM tables
        Base.metadata.create_all(self.engine)

        # Remaining tables managed via raw SQL for simplicity
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS loans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    principal_cents INTEGER NOT NULL,
                    balance_cents INTEGER NOT NULL,
                    interest_rate REAL NOT NULL,
                    term_days INTEGER NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS interest_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    balance_cents INTEGER NOT NULL,
                    interest_rate REAL NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    base_currency TEXT NOT NULL,
                    target_currency TEXT NOT NULL,
                    rate REAL NOT NULL,
                    updated_at TEXT DEFAULT (datetime('now')),
                    PRIMARY KEY (base_currency, target_currency)
                )
                """
            )
            conn.commit()

    # Minimal operations required by tests
    def get_balance(self, user_id: int) -> int:
        with self.SessionLocal() as session:
            account = (
                session.execute(select(Account.balance_cents).where(Account.user_id == user_id))
                .scalar_one_or_none()
            )
            return int(account) if account is not None else 0

    def deposit(self, user_id: int, amount_cents: int, currency: str = "USD") -> int:
        """Deposit funds into a user's account applying configured tax."""
        cfg = get_config()
        tax = int(amount_cents * cfg.tax_rate)
        net = amount_cents - tax
        with self.SessionLocal() as session:  # type: Session
            account = (
                session.execute(select(Account).where(Account.user_id == user_id))
                .scalar_one_or_none()
            )
            if not account:
                account = Account(user_id=user_id, currency=currency, balance_cents=0)
                session.add(account)
                session.flush()
            account.balance_cents += net
            tx = TransactionModel(
                type="deposit",
                amount_cents=net,
                currency=currency,
                dest_account_id=account.id,
            )
            session.add(tx)
            session.flush()
            entry = LedgerEntry(
                account_id=account.id,
                transaction_id=tx.id,
                delta_cents=net,
                balance_after=account.balance_cents,
            )
            session.add(entry)
            session.commit()
            return net

    def withdraw(self, user_id: int, amount_cents: int, currency: str = "USD") -> int:
        """Withdraw funds from a user's account.

        Raises
        ------
        EconomyError
            If the user has insufficient funds or no account.
        """
        with self.SessionLocal() as session:
            account = (
                session.execute(select(Account).where(Account.user_id == user_id))
                .scalar_one_or_none()
            )
            if not account or account.balance_cents < amount_cents:
                raise EconomyError("Insufficient funds")
            account.balance_cents -= amount_cents
            tx = TransactionModel(
                type="withdrawal",
                amount_cents=amount_cents,
                currency=currency,
                src_account_id=account.id,
            )
            session.add(tx)
            session.flush()
            entry = LedgerEntry(
                account_id=account.id,
                transaction_id=tx.id,
                delta_cents=-amount_cents,
                balance_after=account.balance_cents,
            )
            session.add(entry)
            session.commit()
            return account.balance_cents

    def transfer(
        self,
        from_user_id: int,
        to_user_id: int,
        amount_cents: int,
        currency: str = "USD",
    ) -> None:
        """Transfer funds between two user accounts."""
        with self.SessionLocal() as session:
            from_acct = (
                session.execute(select(Account).where(Account.user_id == from_user_id))
                .scalar_one_or_none()
            )
            to_acct = (
                session.execute(select(Account).where(Account.user_id == to_user_id))
                .scalar_one_or_none()
            )
            if not from_acct or from_acct.balance_cents < amount_cents:
                raise EconomyError("Insufficient funds")
            if not to_acct:
                to_acct = Account(user_id=to_user_id, currency=currency, balance_cents=0)
                session.add(to_acct)
                session.flush()
            from_acct.balance_cents -= amount_cents
            to_acct.balance_cents += amount_cents
            tx = TransactionModel(
                type="transfer",
                amount_cents=amount_cents,
                currency=currency,
                src_account_id=from_acct.id,
                dest_account_id=to_acct.id,
            )
            session.add(tx)
            session.flush()
            session.add(
                LedgerEntry(
                    account_id=from_acct.id,
                    transaction_id=tx.id,
                    delta_cents=-amount_cents,
                    balance_after=from_acct.balance_cents,
                )
            )
            session.add(
                LedgerEntry(
                    account_id=to_acct.id,
                    transaction_id=tx.id,
                    delta_cents=amount_cents,
                    balance_after=to_acct.balance_cents,
                )
            )
            session.commit()
            xp_reward_service.grant_hidden_xp(to_user_id, reason="transfer")

    def record_gig_payout(
        self, band_id: int, amount_cents: int, currency: str = "USD"
    ) -> int:
        """Credit gig earnings to a band's account and log the ledger entry."""
        with self.SessionLocal() as session:
            account = (
                session.execute(select(Account).where(Account.user_id == band_id))
                .scalar_one_or_none()
            )
            if not account:
                account = Account(user_id=band_id, currency=currency, balance_cents=0)
                session.add(account)
                session.flush()
            account.balance_cents += amount_cents
            tx = TransactionModel(
                type="gig",
                amount_cents=amount_cents,
                currency=currency,
                dest_account_id=account.id,
            )
            session.add(tx)
            session.flush()
            session.add(
                LedgerEntry(
                    account_id=account.id,
                    transaction_id=tx.id,
                    delta_cents=amount_cents,
                    balance_after=account.balance_cents,
                )
            )
            session.commit()
            return account.balance_cents

    def charge_recording_fee(self, user_id: int, currency: str = "USD") -> int:
        """Deduct recording cost from a user's account and log in the ledger."""
        amount_cents = self.recording_cost
        with self.SessionLocal() as session:
            account = (
                session.execute(select(Account).where(Account.user_id == user_id))
                .scalar_one_or_none()
            )
            if not account or account.balance_cents < amount_cents:
                raise EconomyError("Insufficient funds")
            account.balance_cents -= amount_cents
            tx = TransactionModel(
                type="recording",
                amount_cents=amount_cents,
                currency=currency,
                src_account_id=account.id,
            )
            session.add(tx)
            session.flush()
            entry = LedgerEntry(
                account_id=account.id,
                transaction_id=tx.id,
                delta_cents=-amount_cents,
                balance_after=account.balance_cents,
            )
            session.add(entry)
            session.commit()
            return account.balance_cents

    def list_transactions(self, user_id: int, limit: int = 50) -> list[TransactionRecord]:
        with self.SessionLocal() as session:
            account = (
                session.execute(select(Account.id).where(Account.user_id == user_id))
                .scalar_one_or_none()
            )
            if account is None:
                return []
            q = (
                session.query(TransactionModel)
                .filter(
                    or_(
                        TransactionModel.src_account_id == account,
                        TransactionModel.dest_account_id == account,
                    )
                )
                .order_by(TransactionModel.id.desc())
                .limit(limit)
            )
            rows = q.all()
            return [
                TransactionRecord(
                    id=r.id,
                    type=r.type,
                    amount_cents=r.amount_cents,
                    currency=r.currency,
                    src_account_id=r.src_account_id,
                    dest_account_id=r.dest_account_id,
                    created_at=r.created_at.isoformat() if r.created_at else "",
                )
                for r in rows
            ]

    # --------------- banking extras ---------------

    def open_interest_account(
        self, user_id: int, balance_cents: int, interest_rate: float, currency: str = "USD"
    ) -> int:
        if balance_cents < 0:
            raise EconomyError("balance must be non-negative")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO interest_accounts(user_id, balance_cents, interest_rate, currency)
                VALUES (?,?,?,?)
                """,
                (user_id, balance_cents, interest_rate, currency),
            )
            account_id = int(cur.lastrowid or 0)
            conn.commit()
            return account_id

    def create_loan(self, user_id: int, amount_cents: int, interest_rate: float, term_days: int) -> int:
        if amount_cents <= 0 or interest_rate <= 0 or term_days <= 0:
            raise EconomyError("invalid loan parameters")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO loans(user_id, principal_cents, balance_cents, interest_rate, term_days)
                VALUES (?,?,?,?,?)
                """,
                (user_id, amount_cents, amount_cents, interest_rate, term_days),
            )
            loan_id = int(cur.lastrowid or 0)
            # deposit loan amount without tax
            cur.execute(
                "INSERT OR IGNORE INTO accounts(user_id, currency, balance_cents) VALUES (?,?,0)",
                (user_id, "USD"),
            )
            cur.execute(
                "UPDATE accounts SET balance_cents = balance_cents + ? WHERE user_id = ?",
                (amount_cents, user_id),
            )
            cur.execute(
                "INSERT INTO transactions(type, amount_cents, currency, dest_account_id) VALUES ('loan', ?, 'USD', ?)",
                (amount_cents, user_id),
            )
            tx_id = cur.lastrowid
            cur.execute("SELECT balance_cents FROM accounts WHERE user_id = ?", (user_id,))
            balance = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO ledger_entries(account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, ?, ?)",
                (user_id, tx_id, amount_cents, balance),
            )
            conn.commit()
            return loan_id

    def list_loans(self, user_id: int) -> list[Loan]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM loans WHERE user_id = ?", (user_id,))
            rows = cur.fetchall()
            return [Loan(**dict(r)) for r in rows]

    def calculate_daily_interest(self, account_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT user_id, balance_cents, interest_rate, currency FROM interest_accounts WHERE id = ?",
                (account_id,),
            )
            row = cur.fetchone()
            if not row:
                raise EconomyError("Interest account not found")
            user_id, balance, rate, currency = row
            interest = int(balance * rate)
            if interest <= 0:
                return 0
            cur.execute(
                "UPDATE interest_accounts SET balance_cents = balance_cents + ? WHERE id = ?",
                (interest, account_id),
            )
            cur.execute(
                "INSERT OR IGNORE INTO accounts(user_id, currency, balance_cents) VALUES (?,?,0)",
                (user_id, currency),
            )
            cur.execute(
                "UPDATE accounts SET balance_cents = balance_cents + ? WHERE user_id = ? AND currency = ?",
                (interest, user_id, currency),
            )
            cur.execute(
                "INSERT INTO transactions(type, amount_cents, currency, dest_account_id) VALUES ('interest', ?, ?, ?)",
                (interest, currency, user_id),
            )
            tx_id = cur.lastrowid
            cur.execute(
                "SELECT balance_cents FROM accounts WHERE user_id = ? AND currency = ?",
                (user_id, currency),
            )
            balance_after = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO ledger_entries(account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, ?, ?)",
                (user_id, tx_id, interest, balance_after),
            )
            conn.commit()
            return interest

    def set_exchange_rate(self, base: str, target: str, rate: float) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO exchange_rates(base_currency, target_currency, rate, updated_at)
                VALUES (?,?,?, datetime('now'))
                """,
                (base, target, rate),
            )
            conn.commit()

    def convert_currency(self, amount_cents: int, from_currency: str, to_currency: str) -> int:
        if from_currency == to_currency:
            return amount_cents
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT rate FROM exchange_rates WHERE base_currency = ? AND target_currency = ?",
                (from_currency, to_currency),
            )
            row = cur.fetchone()
            if not row:
                raise EconomyError("Exchange rate not found")
            rate = float(row[0])
            return int(amount_cents * rate)

    def credit_purchase(self, user_id: int, amount_cents: int, premium_currency) -> int:
        """Credit premium currency to a user's ledger after a purchase.

        Parameters
        ----------
        user_id:
            The ID of the user receiving the credit.
        amount_cents:
            Real money amount (in cents) spent by the user.
        premium_currency:
            A :class:`~backend.models.payment.PremiumCurrency` describing the
            currency to credit. Only the ``code`` and ``exchange_rate`` fields
            are required which keeps the function flexible for tests.

        Returns
        -------
        int
            The amount of premium currency units credited.
        """

        # Determine how many premium units correspond to ``amount_cents``.  The
        # ``exchange_rate`` represents how many premium units are granted per
        # 100 cents (i.e. 1 USD).  We floor the result to an integer number of
        # units.
        rate = getattr(premium_currency, "exchange_rate", 1)
        units = amount_cents * int(rate) // 100
        code = getattr(premium_currency, "code", str(premium_currency))

        with self.SessionLocal() as session:
            account = (
                session.execute(select(Account).where(Account.user_id == user_id))
                .scalar_one_or_none()
            )
            if not account:
                account = Account(user_id=user_id, currency=code, balance_cents=0)
                session.add(account)
                session.flush()
            account.balance_cents += units
            tx = TransactionModel(
                type="purchase",
                amount_cents=units,
                currency=code,
                dest_account_id=account.id,
            )
            session.add(tx)
            session.flush()
            session.add(
                LedgerEntry(
                    account_id=account.id,
                    transaction_id=tx.id,
                    delta_cents=units,
                    balance_after=account.balance_cents,
                )
            )
            session.commit()
            return units
