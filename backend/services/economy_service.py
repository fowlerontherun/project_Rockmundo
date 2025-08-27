from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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
            conn.commit()

    # Minimal operations required by tests
    def get_balance(self, user_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT balance_cents FROM accounts WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return int(row[0]) if row else 0

    def deposit(self, user_id: int, amount_cents: int, currency: str = "USD") -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO accounts(user_id, currency, balance_cents) VALUES (?,?,0)",
                (user_id, currency),
            )
            cur.execute(
                "UPDATE accounts SET balance_cents = balance_cents + ? WHERE user_id = ?",
                (amount_cents, user_id),
            )
            conn.commit()
            return amount_cents
