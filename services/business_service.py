"""Service layer for user owned businesses."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from services.skill_service import skill_service

from .economy_service import EconomyError, EconomyService

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class BusinessService:
    def __init__(
        self, db_path: Optional[str] = None, economy: Optional[EconomyService] = None
    ) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.economy = economy or EconomyService(self.db_path)
        self.economy.ensure_schema()
        self.ensure_schema()

    # ---------------- schema ----------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS businesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    business_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    startup_cost INTEGER NOT NULL,
                    revenue_rate INTEGER NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT
                )
                """
            )
            conn.commit()

    # ---------------- helpers ----------------
    def _fetch(self, business_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM businesses WHERE id = ?", (business_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    # ---------------- CRUD ----------------
    def create_business(
        self,
        owner_id: int,
        name: str,
        business_type: str,
        location: str,
        startup_cost: int,
        revenue_rate: int,
    ) -> Dict[str, Any]:
        if startup_cost < 0:
            raise ValueError("startup_cost must be non-negative")
        try:
            self.economy.withdraw(owner_id, startup_cost)
        except EconomyError as e:  # pragma: no cover
            raise ValueError(str(e)) from e
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO businesses (owner_id, name, business_type, location, startup_cost, revenue_rate)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (owner_id, name, business_type, location, startup_cost, revenue_rate),
            )
            conn.commit()
            bid = int(cur.lastrowid or 0)
        return {
            "id": bid,
            "owner_id": owner_id,
            "name": name,
            "business_type": business_type,
            "location": location,
            "startup_cost": startup_cost,
            "revenue_rate": revenue_rate,
        }

    def list_businesses(self, owner_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            q = "SELECT * FROM businesses"
            vals: List[Any] = []
            if owner_id is not None:
                q += " WHERE owner_id = ?"
                vals.append(owner_id)
            cur.execute(q, tuple(vals))
            return [dict(r) for r in cur.fetchall()]

    def update_business(self, business_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not updates:
            return self._fetch(business_id) or {}
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            vals = list(updates.values()) + [business_id]
            cur.execute(
                f"UPDATE businesses SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
                vals,
            )
            if cur.rowcount == 0:
                return {}
            conn.commit()
        return self._fetch(business_id) or {}

    def delete_business(self, business_id: int) -> bool:
        biz = self._fetch(business_id)
        if not biz:
            return False
        refund = int(biz["startup_cost"] / 2)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM businesses WHERE id = ?", (business_id,))
            conn.commit()
        if refund:
            self.economy.deposit(biz["owner_id"], refund)
        return True

    # ---------------- extras ----------------
    def collect_revenue(self, business_id: int) -> int:
        biz = self._fetch(business_id)
        if not biz:
            raise ValueError("Business not found")
        amount = int(biz["revenue_rate"])
        fm_skill = Skill(
            id=SKILL_NAME_TO_ID.get("financial_management", 0),
            name="financial_management",
            category="business",
        )
        level = skill_service.train(biz["owner_id"], fm_skill, 0).level
        amount = int(amount * (1 + 0.05 * max(level - 1, 0)))
        if amount:
            self.economy.deposit(biz["owner_id"], amount)
        return amount

    def get_business(self, business_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch(business_id)

    # investment features
    def invest(self, owner_id: int, amount_cents: int, interest_rate: float) -> int:
        if amount_cents <= 0:
            raise ValueError("amount_cents must be positive")
        self.economy.withdraw(owner_id, amount_cents)
        return self.economy.open_interest_account(owner_id, amount_cents, interest_rate)

    def collect_investment_returns(self, account_id: int) -> int:
        return self.economy.calculate_daily_interest(account_id)
