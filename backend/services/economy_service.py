from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from backend.utils.logging import get_logger
from backend.models.economy_config import get_config

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

    def list_recent_transactions(self, limit: int = 50) -> list[TransactionRecord]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, type, amount_cents, currency, src_account_id, dest_account_id, created_at FROM transactions ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            return [TransactionRecord(**dict(row)) for row in rows]

    def credit_purchase(self, user_id: int, amount_cents: int, currency="USD") -> int:
        """Credit a user's account after successful purchase."""
        code = getattr(currency, "code", currency)
        return self.deposit(user_id, amount_cents, code)
