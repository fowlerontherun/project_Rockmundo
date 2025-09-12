"""Membership service managing tiers and recurring fees."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class MembershipService:
    """Handle membership tiers and user subscriptions."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()

    # ------------------------------------------------------------------
    # schema helpers
    # ------------------------------------------------------------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS membership_tiers (
                    name TEXT PRIMARY KEY,
                    monthly_fee INTEGER NOT NULL,
                    discount REAL NOT NULL
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memberships (
                    user_id INTEGER PRIMARY KEY,
                    tier TEXT NOT NULL,
                    renew_at TEXT NOT NULL,
                    FOREIGN KEY (tier) REFERENCES membership_tiers(name)
                )
                """,
            )
            cur.execute("SELECT COUNT(*) FROM membership_tiers")
            if cur.fetchone()[0] == 0:
                cur.executemany(
                    "INSERT INTO membership_tiers (name, monthly_fee, discount) VALUES (?, ?, ?)",
                    [
                        ("Basic", 0, 0.0),
                        ("Pro", 500, 5.0),
                        ("Elite", 1000, 10.0),
                    ],
                )
            conn.commit()

    # ------------------------------------------------------------------
    # tier helpers
    # ------------------------------------------------------------------
    def list_tiers(self) -> List[Dict[str, float | int | str]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT name, monthly_fee, discount FROM membership_tiers ORDER BY monthly_fee"
            )
            return [dict(r) for r in cur.fetchall()]

    def get_tier(self, name: str) -> Optional[Dict[str, float | int | str]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT name, monthly_fee, discount FROM membership_tiers WHERE name=?",
                (name,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------
    # membership helpers
    # ------------------------------------------------------------------
    def get_membership(self, user_id: int) -> Optional[Dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT user_id, tier, renew_at FROM memberships WHERE user_id=?",
                (user_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def join(self, user_id: int, tier: str) -> int:
        info = self.get_tier(tier)
        if not info:
            raise ValueError("Unknown tier")
        renew_at = (datetime.utcnow() + timedelta(days=30)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO memberships (user_id, tier, renew_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    tier=excluded.tier,
                    renew_at=excluded.renew_at
                """,
                (user_id, tier, renew_at),
            )
            conn.commit()
        return int(info["monthly_fee"])

    def renew(self, user_id: int) -> int:
        membership = self.get_membership(user_id)
        if not membership:
            raise ValueError("No active membership")
        info = self.get_tier(membership["tier"])
        renew_at = (
            datetime.fromisoformat(membership["renew_at"]) + timedelta(days=30)
        ).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE memberships SET renew_at=? WHERE user_id=?",
                (renew_at, user_id),
            )
            conn.commit()
        return int(info["monthly_fee"]) if info else 0

    def cancel(self, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM memberships WHERE user_id=?", (user_id,))
            conn.commit()

    def get_discount(self, user_id: int) -> float:
        membership = self.get_membership(user_id)
        if not membership:
            return 0.0
        info = self.get_tier(membership["tier"])
        return float(info["discount"]) if info else 0.0


membership_service = MembershipService()

__all__ = ["MembershipService", "membership_service"]