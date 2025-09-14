from __future__ import annotations

import sqlite3

from models.banking import InterestAccount, Loan
from backend.utils.logging import get_logger
from .economy_service import EconomyService, EconomyError

logger = get_logger(__name__)


class BankService:
    """Service providing simple banking operations."""

    def __init__(self, economy: EconomyService):
        self.economy = economy

    # internal --------------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        """Return a connection to the shared economy database."""
        return sqlite3.connect(self.economy.db_path)

    # savings accounts ------------------------------------------------------
    def create_savings_account(
        self, user_id: int, interest_rate: float = 0.01, currency: str = "USD"
    ) -> InterestAccount:
        """Create or fetch a savings account for the user."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, user_id, balance_cents, interest_rate, currency, created_at "
                "FROM interest_accounts WHERE user_id = ?",
                (user_id,),
            )
            row = cur.fetchone()
            if row:
                return InterestAccount(*row)
            cur.execute(
                "INSERT INTO interest_accounts (user_id, balance_cents, interest_rate, currency) "
                "VALUES (?, 0, ?, ?)",
                (user_id, interest_rate, currency),
            )
            acct_id = cur.lastrowid
            conn.commit()
            cur.execute(
                "SELECT id, user_id, balance_cents, interest_rate, currency, created_at "
                "FROM interest_accounts WHERE id = ?",
                (acct_id,),
            )
            row = cur.fetchone()
        return InterestAccount(*row)

    def deposit_to_savings(self, user_id: int, amount_cents: int) -> int:
        """Move funds from the user's main account into their savings account."""
        # Withdraw from main account first to ensure sufficient funds
        self.economy.withdraw(user_id, amount_cents)
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE interest_accounts SET balance_cents = balance_cents + ? "
                "WHERE user_id = ?",
                (amount_cents, user_id),
            )
            if cur.rowcount == 0:
                raise EconomyError("Savings account not found")
            cur.execute(
                "SELECT balance_cents FROM interest_accounts WHERE user_id = ?",
                (user_id,),
            )
            balance = cur.fetchone()[0]
            conn.commit()
        return balance

    def withdraw_from_savings(self, user_id: int, amount_cents: int) -> int:
        """Move funds from savings back to the user's main account."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT balance_cents FROM interest_accounts WHERE user_id = ?",
                (user_id,),
            )
            row = cur.fetchone()
            if not row or row[0] < amount_cents:
                raise EconomyError("Insufficient savings balance")
            cur.execute(
                "UPDATE interest_accounts SET balance_cents = balance_cents - ? "
                "WHERE user_id = ?",
                (amount_cents, user_id),
            )
            balance = row[0] - amount_cents
            conn.commit()
        # Deposit back into main account
        self.economy.deposit(user_id, amount_cents)
        return balance

    def accrue_interest(self) -> None:
        """Apply interest to all savings accounts."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, balance_cents, interest_rate FROM interest_accounts"
            )
            accounts = cur.fetchall()
            for acct_id, balance, rate in accounts:
                interest = int(balance * rate)
                if interest > 0:
                    cur.execute(
                        "UPDATE interest_accounts SET balance_cents = balance_cents + ? "
                        "WHERE id = ?",
                        (interest, acct_id),
                    )
            conn.commit()

    # loans -----------------------------------------------------------------
    def issue_loan(
        self, user_id: int, principal_cents: int, interest_rate: float, term_days: int
    ) -> Loan:
        """Issue a loan and deposit the funds into the user's account."""
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO loans (user_id, principal_cents, balance_cents, interest_rate, term_days) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, principal_cents, principal_cents, interest_rate, term_days),
            )
            loan_id = cur.lastrowid
            conn.commit()
            cur.execute(
                "SELECT id, user_id, principal_cents, balance_cents, interest_rate, term_days, created_at "
                "FROM loans WHERE id = ?",
                (loan_id,),
            )
            row = cur.fetchone()
        # Deposit the principal into the user's main account
        self.economy.deposit(user_id, principal_cents)
        return Loan(*row)

    def repay_loan(self, loan_id: int, user_id: int, amount_cents: int) -> int:
        """Repay part of a loan by withdrawing from the user's account."""
        # Withdraw funds from the user's main account
        self.economy.withdraw(user_id, amount_cents)
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT balance_cents FROM loans WHERE id = ? AND user_id = ?",
                (loan_id, user_id),
            )
            row = cur.fetchone()
            if not row:
                raise EconomyError("Loan not found")
            new_balance = max(0, row[0] - amount_cents)
            cur.execute(
                "UPDATE loans SET balance_cents = ? WHERE id = ?",
                (new_balance, loan_id),
            )
            conn.commit()
        return new_balance
