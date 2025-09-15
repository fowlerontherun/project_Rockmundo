from __future__ import annotations

"""Service layer for a simple item marketplace with bidding."""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from services.economy_service import EconomyService, EconomyError

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class MarketplaceError(Exception):
    pass


class MarketplaceService:
    def __init__(self, db_path: Optional[str] = None, economy: Optional[EconomyService] = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.economy = economy or EconomyService(db_path=self.db_path)

    # --------------------------- schema ---------------------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS marketplace_listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    seller_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    current_price_cents INTEGER NOT NULL,
                    highest_bidder_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS marketplace_bids (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id INTEGER NOT NULL,
                    bidder_id INTEGER NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
            conn.commit()

    # --------------------------- helpers ---------------------------
    def _get_listing(self, cur: sqlite3.Cursor, listing_id: int) -> Dict:
        cur.execute("SELECT * FROM marketplace_listings WHERE id = ?", (listing_id,))
        row = cur.fetchone()
        if not row:
            raise MarketplaceError("Listing not found")
        columns = [d[0] for d in cur.description]
        return dict(zip(columns, row))

    # --------------------------- listings ---------------------------
    def create_listing(self, seller_id: int, title: str, description: str, starting_price_cents: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO marketplace_listings (seller_id, title, description, current_price_cents)
                VALUES (?, ?, ?, ?)
                """,
                (seller_id, title, description, starting_price_cents),
            )
            conn.commit()
            return int(cur.lastrowid or 0)

    def list_active(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM marketplace_listings WHERE status = 'active' ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]

    def get_listing(self, listing_id: int) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM marketplace_listings WHERE id = ?", (listing_id,))
            row = cur.fetchone()
            if not row:
                raise MarketplaceError("Listing not found")
            return dict(row)

    def delete_listing(self, listing_id: int, user_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM marketplace_listings WHERE id = ? AND seller_id = ? AND status = 'active'",
                (listing_id, user_id),
            )
            if cur.rowcount == 0:
                raise MarketplaceError("Listing not found or cannot be deleted")
            conn.commit()

    # --------------------------- bidding ---------------------------
    def place_bid(self, listing_id: int, bidder_id: int, amount_cents: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            listing = self._get_listing(cur, listing_id)
            if listing["status"] != "active":
                raise MarketplaceError("Listing not active")
            if amount_cents <= listing["current_price_cents"]:
                raise MarketplaceError("Bid must be higher than current price")
            cur.execute(
                "INSERT INTO marketplace_bids (listing_id, bidder_id, amount_cents) VALUES (?, ?, ?)",
                (listing_id, bidder_id, amount_cents),
            )
            cur.execute(
                "UPDATE marketplace_listings SET current_price_cents = ?, highest_bidder_id = ? WHERE id = ?",
                (amount_cents, bidder_id, listing_id),
            )
            conn.commit()

    # --------------------------- purchasing ---------------------------
    def purchase(self, listing_id: int, buyer_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            listing = self._get_listing(cur, listing_id)
            if listing["status"] != "active":
                raise MarketplaceError("Listing not active")
            if listing.get("highest_bidder_id") != buyer_id:
                raise MarketplaceError("Only highest bidder can purchase")
            try:
                self.economy.transfer(buyer_id, listing["seller_id"], listing["current_price_cents"])
            except EconomyError as exc:
                raise MarketplaceError(str(exc))
            cur.execute("UPDATE marketplace_listings SET status = 'sold' WHERE id = ?", (listing_id,))
            conn.commit()
