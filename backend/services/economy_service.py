from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from services.xp_reward_service import xp_reward_service

from backend.models.banking import Loan
from backend.models.economy_config import get_config
from backend.utils.logging import get_logger

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

    # ---------------- schema ----------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    balance_cents INTEGER NOT NULL DEFAULT 0,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    src_account_id INTEGER,
                    dest_account_id INTEGER,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY(src_account_id) REFERENCES accounts(id),
                    FOREIGN KEY(dest_account_id) REFERENCES accounts(id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS ledger_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    transaction_id INTEGER NOT NULL,
                    delta_cents INTEGER NOT NULL,
                    balance_after INTEGER NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY(account_id) REFERENCES accounts(id),
                    FOREIGN KEY(transaction_id) REFERENCES transactions(id)
                )
                """
            )
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
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT balance_cents FROM accounts WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return int(row[0]) if row else 0

    def deposit(self, user_id: int, amount_cents: int, currency: str = "USD") -> int:
        """Deposit funds into a user's account applying configured tax."""
        cfg = get_config()
        tax = int(amount_cents * cfg.tax_rate)
        net = amount_cents - tax
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO accounts(user_id, currency, balance_cents) VALUES (?,?,0)",
                (user_id, currency),
            )
            cur.execute(
                "UPDATE accounts SET balance_cents = balance_cents + ? WHERE user_id = ?",
                (net, user_id),
            )
            cur.execute(
                "INSERT INTO transactions(type, amount_cents, currency, dest_account_id) VALUES ('deposit', ?, ?, ?)",
                (net, currency, user_id),
            )
            tx_id = cur.lastrowid
            cur.execute("SELECT balance_cents FROM accounts WHERE user_id = ?", (user_id,))
            balance = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO ledger_entries(account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, ?, ?)",
                (user_id, tx_id, net, balance),
            )
            conn.commit()
            return net

    def withdraw(self, user_id: int, amount_cents: int, currency: str = "USD") -> int:
        """Withdraw funds from a user's account.

        Raises
        ------
        EconomyError
            If the user has insufficient funds or no account.
        """
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT balance_cents FROM accounts WHERE user_id = ? AND currency = ?",
                (user_id, currency),
            )
            row = cur.fetchone()
            balance = int(row[0]) if row else 0
            if balance < amount_cents:
                raise EconomyError("Insufficient funds")
            cur.execute(
                "UPDATE accounts SET balance_cents = balance_cents - ? WHERE user_id = ? AND currency = ?",
                (amount_cents, user_id, currency),
            )
            cur.execute(
                "INSERT INTO transactions(type, amount_cents, currency, src_account_id) VALUES ('withdrawal', ?, ?, ?)",
                (amount_cents, currency, user_id),
            )
            tx_id = cur.lastrowid
            cur.execute(
                "SELECT balance_cents FROM accounts WHERE user_id = ? AND currency = ?",
                (user_id, currency),
            )
            balance_after = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO ledger_entries(account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, ?, ?)",
                (user_id, tx_id, -amount_cents, balance_after),
            )
            conn.commit()
            return balance_after

    def transfer(
        self,
        from_user_id: int,
        to_user_id: int,
        amount_cents: int,
        currency: str = "USD",
    ) -> None:
        """Transfer funds between two user accounts."""
        self.withdraw(from_user_id, amount_cents, currency)
        # deposit without applying tax; use direct update
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO accounts(user_id, currency, balance_cents) VALUES (?,?,0)",
                (to_user_id, currency),
            )
            cur.execute(
                "UPDATE accounts SET balance_cents = balance_cents + ? WHERE user_id = ? AND currency = ?",
                (amount_cents, to_user_id, currency),
            )
            cur.execute(
                "INSERT INTO transactions(type, amount_cents, currency, src_account_id, dest_account_id) VALUES ('transfer', ?, ?, ?, ?)",
                (amount_cents, currency, from_user_id, to_user_id),
            )
            tx_id = cur.lastrowid
            cur.execute(
                "SELECT balance_cents FROM accounts WHERE user_id = ? AND currency = ?",
                (from_user_id, currency),
            )
            from_balance = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO ledger_entries(account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, ?, ?)",
                (from_user_id, tx_id, -amount_cents, from_balance),
            )
            cur.execute(
                "SELECT balance_cents FROM accounts WHERE user_id = ? AND currency = ?",
                (to_user_id, currency),
            )
            to_balance = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO ledger_entries(account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, ?, ?)",
                (to_user_id, tx_id, amount_cents, to_balance),
            )
            conn.commit()
            xp_reward_service.grant_hidden_xp(to_user_id, reason="transfer")

    def list_transactions(self, user_id: int, limit: int = 50) -> list[TransactionRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, type, amount_cents, currency, src_account_id, dest_account_id, created_at FROM transactions WHERE src_account_id = ? OR dest_account_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, user_id, limit),
            )
            rows = cur.fetchall()
            return [TransactionRecord(**dict(row)) for row in rows]

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

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            # Ensure the user account exists.  We store premium currency in the
            # same accounts table keyed by ``user_id``.  ``INSERT OR IGNORE``
            # allows re-use of an existing account without raising.
            cur.execute(
                "INSERT OR IGNORE INTO accounts(user_id, currency, balance_cents) VALUES (?,?,0)",
                (user_id, code),
            )
            # Update the balance and record the purchase transaction.
            cur.execute(
                "UPDATE accounts SET balance_cents = balance_cents + ? WHERE user_id = ?",
                (units, user_id),
            )
            cur.execute(
                "INSERT INTO transactions(type, amount_cents, currency, dest_account_id) VALUES ('purchase', ?, ?, ?)",
                (units, code, user_id),
            )
            tx_id = cur.lastrowid
            # Write a ledger entry reflecting the new balance.
            cur.execute("SELECT balance_cents FROM accounts WHERE user_id = ?", (user_id,))
            balance = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO ledger_entries(account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, ?, ?)",
                (user_id, tx_id, units, balance),
            )
            conn.commit()
            return units
