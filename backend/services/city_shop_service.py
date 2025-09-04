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
                    restock_interval INTEGER,
                    restock_quantity INTEGER,
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
                    restock_interval INTEGER,
                    restock_quantity INTEGER,
                    PRIMARY KEY (shop_id, book_id),
                    FOREIGN KEY (shop_id) REFERENCES city_shops(id) ON DELETE CASCADE
                )
                """,
            )
            # ensure restock columns exist for legacy DBs
            for tbl in ("shop_items", "shop_books"):
                cur.execute(f"PRAGMA table_info({tbl})")
                cols = {row[1] for row in cur.fetchall()}
                if "restock_interval" not in cols:
                    cur.execute(f"ALTER TABLE {tbl} ADD COLUMN restock_interval INTEGER")
                if "restock_quantity" not in cols:
                    cur.execute(f"ALTER TABLE {tbl} ADD COLUMN restock_quantity INTEGER")
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
        self,
        shop_id: int,
        item_id: int,
        quantity: int = 1,
        restock_interval: int | None = None,
        restock_quantity: int | None = None,
    ) -> None:
        if quantity < 0:
            raise ValueError("quantity must be non-negative")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO shop_items (shop_id, item_id, quantity, restock_interval, restock_quantity)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(shop_id, item_id) DO UPDATE SET
                    quantity = quantity + excluded.quantity,
                    restock_interval = COALESCE(excluded.restock_interval, restock_interval),
                    restock_quantity = COALESCE(excluded.restock_quantity, restock_quantity)
                """,
                (shop_id, item_id, quantity, restock_interval, restock_quantity),
            )
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
                "SELECT item_id, quantity, restock_interval, restock_quantity FROM shop_items WHERE shop_id = ?",
                (shop_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # inventory operations - books
    # ------------------------------------------------------------------
    def add_book(
        self,
        shop_id: int,
        book_id: int,
        quantity: int = 1,
        restock_interval: int | None = None,
        restock_quantity: int | None = None,
    ) -> None:
        if quantity < 0:
            raise ValueError("quantity must be non-negative")
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO shop_books (shop_id, book_id, quantity, restock_interval, restock_quantity)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(shop_id, book_id) DO UPDATE SET
                    quantity = quantity + excluded.quantity,
                    restock_interval = COALESCE(excluded.restock_interval, restock_interval),
                    restock_quantity = COALESCE(excluded.restock_quantity, restock_quantity)
                """,
                (shop_id, book_id, quantity, restock_interval, restock_quantity),
            )
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
                "SELECT book_id, quantity, restock_interval, restock_quantity FROM shop_books WHERE shop_id = ?",
                (shop_id,),
            )
            return [dict(r) for r in cur.fetchall()]

    def set_item_restock(
        self, shop_id: int, item_id: int, interval: int | None, quantity: int | None
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE shop_items SET restock_interval = ?, restock_quantity = ? WHERE shop_id = ? AND item_id = ?",
                (interval, quantity, shop_id, item_id),
            )
            conn.commit()

    def set_book_restock(
        self, shop_id: int, book_id: int, interval: int | None, quantity: int | None
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE shop_books SET restock_interval = ?, restock_quantity = ? WHERE shop_id = ? AND book_id = ?",
                (interval, quantity, shop_id, book_id),
            )
            conn.commit()


city_shop_service = CityShopService()

__all__ = ["CityShopService", "city_shop_service"]
