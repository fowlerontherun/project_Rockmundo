"""EconomyService provides basic account and transaction management."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from backend.models.payment import PremiumCurrency
from backend.models.economy_config import get_config

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
            conn.commit()

    # ---------------- helpers ----------------
    def _get_account(self, cur: sqlite3.Cursor, user_id: int) -> Optional[int]:
        cur.execute("SELECT id FROM accounts WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return int(row[0]) if row else None

    def _require_account(self, cur: sqlite3.Cursor, user_id: int, currency: str) -> int:
        acc_id = self._get_account(cur, user_id)
        if acc_id is None:
            cur.execute(
                "INSERT INTO accounts (user_id, currency) VALUES (?, ?)",
                (user_id, currency),
            )
            acc_id = int(cur.lastrowid or 0)
        cur.execute("SELECT currency FROM accounts WHERE id = ?", (acc_id,))
        row = cur.fetchone()
        if row and row[0] != currency:
            raise EconomyError("Currency mismatch for account")
        return acc_id

    def get_balance(self, user_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT balance_cents FROM accounts WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return int(row[0]) if row else 0

    # ---------------- operations ----------------
    def deposit(self, user_id: int, amount_cents: int, currency: str = "USD") -> int:
        if amount_cents <= 0:
            raise EconomyError("Deposit must be positive")
        cfg = get_config()
        # apply inflation then tax
        amount_cents = int(amount_cents * (1 + cfg.inflation_rate))
        net = int(amount_cents * (1 - cfg.tax_rate))
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            acc_id = self._require_account(cur, user_id, currency)
            cur.execute(
                "INSERT INTO transactions (type, amount_cents, currency, dest_account_id) VALUES ('deposit', ?, ?, ?)",
                (net, currency, acc_id),
            )
            tid = int(cur.lastrowid or 0)
            cur.execute(
                "UPDATE accounts SET balance_cents = balance_cents + ? WHERE id = ?",
                (net, acc_id),
            )
            cur.execute("SELECT balance_cents FROM accounts WHERE id = ?", (acc_id,))
            balance = int(cur.fetchone()[0])
            cur.execute(
                "INSERT INTO ledger_entries (account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, ?, ?)",
                (acc_id, tid, net, balance),
            )
            conn.commit()
            return tid

    def withdraw(self, user_id: int, amount_cents: int, currency: str = "USD") -> int:
        if amount_cents <= 0:
            raise EconomyError("Withdrawal must be positive")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            acc_id = self._require_account(cur, user_id, currency)
            cur.execute("SELECT balance_cents FROM accounts WHERE id = ?", (acc_id,))
            balance = int(cur.fetchone()[0])
            if balance < amount_cents:
                raise EconomyError("Insufficient funds")
            cur.execute(
                "INSERT INTO transactions (type, amount_cents, currency, src_account_id) VALUES ('withdrawal', ?, ?, ?)",
                (amount_cents, currency, acc_id),
            )
            tid = int(cur.lastrowid or 0)
            cur.execute(
                "UPDATE accounts SET balance_cents = balance_cents - ? WHERE id = ?",
                (amount_cents, acc_id),
            )
            balance -= amount_cents
            cur.execute(
                "INSERT INTO ledger_entries (account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, ?, ?)",
                (acc_id, tid, -amount_cents, balance),
            )
            conn.commit()
            return tid

    def transfer(self, from_user: int, to_user: int, amount_cents: int, currency: str = "USD") -> int:
        if amount_cents <= 0:
            raise EconomyError("Transfer amount must be positive")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            src_id = self._require_account(cur, from_user, currency)
            dest_id = self._require_account(cur, to_user, currency)
            cur.execute("SELECT balance_cents FROM accounts WHERE id = ?", (src_id,))
            balance = int(cur.fetchone()[0])
            if balance < amount_cents:
                raise EconomyError("Insufficient funds")
            cur.execute(
                "INSERT INTO transactions (type, amount_cents, currency, src_account_id, dest_account_id) VALUES ('transfer', ?, ?, ?, ?)",
                (amount_cents, currency, src_id, dest_id),
            )
            tid = int(cur.lastrowid or 0)
            # update accounts
            cur.execute(
                "UPDATE accounts SET balance_cents = balance_cents - ? WHERE id = ?",
                (amount_cents, src_id),
            )
            cur.execute(
                "UPDATE accounts SET balance_cents = balance_cents + ? WHERE id = ?",
                (amount_cents, dest_id),
            )
            # ledger entries
            cur.execute("SELECT balance_cents FROM accounts WHERE id = ?", (src_id,))
            src_balance = int(cur.fetchone()[0])
            cur.execute(
                "INSERT INTO ledger_entries (account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, ?, ?)",
                (src_id, tid, -amount_cents, src_balance),
            )
            cur.execute("SELECT balance_cents FROM accounts WHERE id = ?", (dest_id,))
            dest_balance = int(cur.fetchone()[0])
            cur.execute(
                "INSERT INTO ledger_entries (account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, ?, ?)",
                (dest_id, tid, amount_cents, dest_balance),
            )
            conn.commit()
            return tid

    def credit_purchase(self, user_id: int, amount_cents: int, currency: PremiumCurrency) -> int:
        """Convert real money into premium currency and deposit it."""
        coins = (amount_cents // 100) * currency.exchange_rate
        if coins <= 0:
            raise EconomyError('Purchase amount too low')
        return self.deposit(user_id, coins, currency=currency.code)

    # ---------------- queries ----------------
    def list_transactions(self, user_id: int, limit: int = 50) -> List[TransactionRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                """
                SELECT t.* FROM transactions t
                JOIN ledger_entries le ON le.transaction_id = t.id
                JOIN accounts a ON a.id = le.account_id
                WHERE a.user_id = ?
                ORDER BY t.created_at DESC, t.id DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = cur.fetchall()
            return [TransactionRecord(**dict(r)) for r in rows]

    def list_recent_transactions(self, limit: int = 50) -> List[TransactionRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM transactions ORDER BY created_at DESC, id DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            return [TransactionRecord(**dict(r)) for r in rows]
