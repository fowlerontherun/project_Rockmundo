"""Service for managing city shops and their inventories."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class CityShopService:
    """Persistent store for shops per city with item and book inventories."""

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
                CREATE TABLE IF NOT EXISTS city_shops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS shop_items (
                    shop_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price_cents INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (shop_id, item_id),
                    FOREIGN KEY (shop_id) REFERENCES city_shops(id) ON DELETE CASCADE
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS shop_books (
                    shop_id INTEGER NOT NULL,
                    book_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price_cents INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (shop_id, book_id),
                    FOREIGN KEY (shop_id) REFERENCES city_shops(id) ON DELETE CASCADE
                )
                """,
            )
            # ensure new columns exist if DB was created before
            cur.execute("PRAGMA table_info(shop_items)")
            cols = [row[1] for row in cur.fetchall()]
            if "price_cents" not in cols:
                cur.execute(
                    "ALTER TABLE shop_items ADD COLUMN price_cents INTEGER NOT NULL DEFAULT 0"
                )
            cur.execute("PRAGMA table_info(shop_books)")
            cols = [row[1] for row in cur.fetchall()]
            if "price_cents" not in cols:
                cur.execute(
                    "ALTER TABLE shop_books ADD COLUMN price_cents INTEGER NOT NULL DEFAULT 0"
                )
            conn.commit()

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _fetch(self, shop_id: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM city_shops WHERE id = ?", (shop_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def create_shop(self, city: str, name: str) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO city_shops (city, name) VALUES (?, ?)",
                (city, name),
            )
            conn.commit()
            sid = int(cur.lastrowid or 0)
        return {"id": sid, "city": city, "name": name}

    def list_shops(self, city: str | None = None) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            q = "SELECT * FROM city_shops"
            params: List[Any] = []
            if city:
                q += " WHERE city = ?"
                params.append(city)
            cur.execute(q, params)
            return [dict(r) for r in cur.fetchall()]

    def update_shop(self, shop_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        if not updates:
            return self._fetch(shop_id) or {}
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [shop_id]
            cur.execute(
                f"UPDATE city_shops SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
                values,
            )
            if cur.rowcount == 0:
                return {}
            conn.commit()
        return self._fetch(shop_id) or {}

    def delete_shop(self, shop_id: int) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM city_shops WHERE id = ?", (shop_id,))
            deleted = cur.rowcount
            if deleted:
                cur.execute("DELETE FROM shop_items WHERE shop_id = ?", (shop_id,))
                cur.execute("DELETE FROM shop_books WHERE shop_id = ?", (shop_id,))
            conn.commit()
        return bool(deleted)

    def get_shop(self, shop_id: int) -> Optional[Dict[str, Any]]:
        return self._fetch(shop_id)

    # ------------------------------------------------------------------
    # inventory operations - items
    # ------------------------------------------------------------------
    def add_item(
        self, shop_id: int, item_id: int, quantity: int = 1, price_cents: int = 0
    ) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO shop_items (shop_id, item_id, quantity, price_cents)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(shop_id, item_id) DO UPDATE SET
                    quantity = quantity + excluded.quantity,
                    price_cents = excluded.price_cents
                """,
                (shop_id, item_id, quantity, price_cents),
            )
            conn.commit()

    def update_item(
        self,
        shop_id: int,
        item_id: int,
        *,
        quantity: int | None = None,
        price_cents: int | None = None,
    ) -> None:
        if quantity is None and price_cents is None:
            return
        if quantity is not None and quantity <= 0:
            raise ValueError("quantity must be positive")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            sets: list[str] = []
            params: list[Any] = []
            if quantity is not None:
                sets.append("quantity = ?")
                params.append(quantity)
            if price_cents is not None:
                sets.append("price_cents = ?")
                params.append(price_cents)
            params.extend([shop_id, item_id])
            cur.execute(
                f"UPDATE shop_items SET {', '.join(sets)} WHERE shop_id = ? AND item_id = ?",
                params,
            )
            if cur.rowcount == 0:
                raise ValueError("item not found")
            conn.commit()

    def remove_item(self, shop_id: int, item_id: int, quantity: int = 1) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT quantity FROM shop_items WHERE shop_id = ? AND item_id = ?",
                (shop_id, item_id),
            )
            row = cur.fetchone()
            if not row or row[0] < quantity:
                raise ValueError("not enough items")
            new_qty = row[0] - quantity
            if new_qty > 0:
                cur.execute(
                    "UPDATE shop_items SET quantity = ? WHERE shop_id = ? AND item_id = ?",
                    (new_qty, shop_id, item_id),
                )
            else:
                cur.execute(
                    "DELETE FROM shop_items WHERE shop_id = ? AND item_id = ?",
                    (shop_id, item_id),
                )
            conn.commit()

    def list_items(self, shop_id: int) -> List[Dict[str, int]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT item_id, quantity, price_cents FROM shop_items WHERE shop_id = ?",
                (shop_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # inventory operations - books
    # ------------------------------------------------------------------
    def add_book(
        self, shop_id: int, book_id: int, quantity: int = 1, price_cents: int = 0
    ) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO shop_books (shop_id, book_id, quantity, price_cents)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(shop_id, book_id) DO UPDATE SET
                    quantity = quantity + excluded.quantity,
                    price_cents = excluded.price_cents
                """,
                (shop_id, book_id, quantity, price_cents),
            )
            conn.commit()

    def update_book(
        self,
        shop_id: int,
        book_id: int,
        *,
        quantity: int | None = None,
        price_cents: int | None = None,
    ) -> None:
        if quantity is None and price_cents is None:
            return
        if quantity is not None and quantity <= 0:
            raise ValueError("quantity must be positive")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            sets: list[str] = []
            params: list[Any] = []
            if quantity is not None:
                sets.append("quantity = ?")
                params.append(quantity)
            if price_cents is not None:
                sets.append("price_cents = ?")
                params.append(price_cents)
            params.extend([shop_id, book_id])
            cur.execute(
                f"UPDATE shop_books SET {', '.join(sets)} WHERE shop_id = ? AND book_id = ?",
                params,
            )
            if cur.rowcount == 0:
                raise ValueError("book not found")
            conn.commit()

    def remove_book(self, shop_id: int, book_id: int, quantity: int = 1) -> None:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT quantity FROM shop_books WHERE shop_id = ? AND book_id = ?",
                (shop_id, book_id),
            )
            row = cur.fetchone()
            if not row or row[0] < quantity:
                raise ValueError("not enough books")
            new_qty = row[0] - quantity
            if new_qty > 0:
                cur.execute(
                    "UPDATE shop_books SET quantity = ? WHERE shop_id = ? AND book_id = ?",
                    (new_qty, shop_id, book_id),
                )
            else:
                cur.execute(
                    "DELETE FROM shop_books WHERE shop_id = ? AND book_id = ?",
                    (shop_id, book_id),
                )
            conn.commit()

    def list_books(self, shop_id: int) -> List[Dict[str, int]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT book_id, quantity, price_cents FROM shop_books WHERE shop_id = ?",
                (shop_id,),
            )
            return [dict(r) for r in cur.fetchall()]


city_shop_service = CityShopService()

__all__ = ["CityShopService", "city_shop_service"]
