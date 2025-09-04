"""Simple loyalty points and tier discount service."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class LoyaltyService:
    """Track customer loyalty points per shop and tier discounts."""

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
                CREATE TABLE IF NOT EXISTS loyalty_points (
                    customer_id INTEGER NOT NULL,
                    shop_id INTEGER NOT NULL,
                    points INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (customer_id, shop_id)
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS loyalty_tiers (
                    name TEXT PRIMARY KEY,
                    threshold INTEGER NOT NULL,
                    discount REAL NOT NULL
                )
                """,
            )
            # seed default tiers if empty
            cur.execute("SELECT COUNT(*) FROM loyalty_tiers")
            if cur.fetchone()[0] == 0:
                cur.executemany(
                    "INSERT INTO loyalty_tiers (name, threshold, discount) VALUES (?, ?, ?)",
                    [
                        ("Bronze", 0, 0.0),
                        ("Silver", 100, 5.0),
                        ("Gold", 500, 10.0),
                    ],
                )
            conn.commit()

    # ------------------------------------------------------------------
    # point helpers
    # ------------------------------------------------------------------
    def get_points(self, customer_id: int, shop_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT points FROM loyalty_points WHERE customer_id=? AND shop_id=?",
                (customer_id, shop_id),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0

    def add_points(self, customer_id: int, shop_id: int, points: int) -> None:
        if points <= 0:
            return
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO loyalty_points (customer_id, shop_id, points)
                VALUES (?, ?, ?)
                ON CONFLICT(customer_id, shop_id) DO UPDATE SET
                    points = points + excluded.points
                """,
                (customer_id, shop_id, points),
            )
            conn.commit()

    def points_for_purchase(self, amount_cents: int) -> int:
        """Return points earned for a purchase amount."""
        return amount_cents // 100

    # ------------------------------------------------------------------
    # tier helpers
    # ------------------------------------------------------------------
    def list_tiers(self) -> List[Dict[str, float | int | str]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT name, threshold, discount FROM loyalty_tiers ORDER BY threshold"
            )
            return [dict(r) for r in cur.fetchall()]

    def set_tier(self, name: str, threshold: int, discount: float) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO loyalty_tiers (name, threshold, discount)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    threshold = excluded.threshold,
                    discount = excluded.discount
                """,
                (name, threshold, discount),
            )
            conn.commit()

    def delete_tier(self, name: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM loyalty_tiers WHERE name = ?", (name,))
            conn.commit()
            return bool(cur.rowcount)

    def get_discount(self, customer_id: int, shop_id: int) -> float:
        points = self.get_points(customer_id, shop_id)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT discount FROM loyalty_tiers WHERE threshold <= ? ORDER BY threshold DESC LIMIT 1",
                (points,),
            )
            row = cur.fetchone()
            return float(row[0]) if row else 0.0


loyalty_service = LoyaltyService()
