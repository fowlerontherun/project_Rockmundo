"""Service layer for generic items and inventories backed by SQLite."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List

from backend.models.item import Item, ItemCategory
from backend.services.addiction_service import addiction_service

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class ItemService:
    """Persistence-backed management of items and user inventories."""

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
                CREATE TABLE IF NOT EXISTS item_categories (
                    name TEXT PRIMARY KEY,
                    description TEXT
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    stats_json TEXT DEFAULT '{}',
                    price_cents INTEGER DEFAULT 0,
                    stock INTEGER DEFAULT 0,
                    FOREIGN KEY (category) REFERENCES item_categories(name)
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_items (
                    user_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    durability INTEGER NOT NULL DEFAULT 100,
                    PRIMARY KEY (user_id, item_id),
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
                """,
            )
            # Ensure durability column exists for legacy tables
            cur.execute("PRAGMA table_info(user_items)")
            cols = [r[1] for r in cur.fetchall()]
            if "durability" not in cols:
                cur.execute(
                    "ALTER TABLE user_items ADD COLUMN durability INTEGER NOT NULL DEFAULT 100"
                )
            conn.commit()

    # ------------------------------------------------------------------
    # Category operations
    # ------------------------------------------------------------------
    def list_categories(self) -> List[ItemCategory]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT name, description FROM item_categories")
            return [ItemCategory(**dict(r)) for r in cur.fetchall()]

    def create_category(self, category: ItemCategory) -> ItemCategory:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO item_categories (name, description) VALUES (?, ?)",
                (category.name, category.description),
            )
            conn.commit()
        return category

    def delete_category(self, name: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM item_categories WHERE name = ?", (name,))
            conn.commit()

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def _row_to_item(self, row: sqlite3.Row) -> Item:
        data = dict(row)
        data["stats"] = json.loads(data.get("stats_json") or "{}")
        data.pop("stats_json", None)
        return Item(**data)

    def list_items(self) -> List[Item]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, category, stats_json, price_cents, stock FROM items"
            )
            return [self._row_to_item(r) for r in cur.fetchall()]

    def create_item(self, item: Item) -> Item:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO items (name, category, stats_json, price_cents, stock)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    item.name,
                    item.category,
                    json.dumps(item.stats),
                    item.price_cents,
                    item.stock,
                ),
            )
            item.id = int(cur.lastrowid or 0)
            conn.commit()
        return item

    def get_item(self, item_id: int) -> Item:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, category, stats_json, price_cents, stock FROM items WHERE id = ?",
                (item_id,),
            )
            row = cur.fetchone()
        if not row:
            raise ValueError("Item not found")
        return self._row_to_item(row)

    def update_item(self, item_id: int, **changes) -> Item:
        if not changes:
            return self.get_item(item_id)
        updates: Dict[str, object] = {}
        params: List[object] = []
        for k, v in changes.items():
            if v is not None and k in {"name", "category", "stats", "price_cents", "stock"}:
                if k == "stats":
                    updates["stats_json"] = json.dumps(v)
                else:
                    updates[k] = v
        if not updates:
            return self.get_item(item_id)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [item_id]
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"UPDATE items SET {set_clause} WHERE id = ?",
                params,
            )
            if cur.rowcount == 0:
                raise ValueError("Item not found")
            conn.commit()
        return self.get_item(item_id)

    def delete_item(self, item_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM items WHERE id = ?", (item_id,))
            cur.execute("DELETE FROM user_items WHERE item_id = ?", (item_id,))
            conn.commit()

    def decrement_stock(self, item_id: int, quantity: int = 1) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT stock FROM items WHERE id = ?", (item_id,))
            row = cur.fetchone()
            if not row or row[0] < quantity:
                raise ValueError("not enough stock")
            cur.execute(
                "UPDATE items SET stock = stock - ? WHERE id = ?",
                (quantity, item_id),
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Inventory management
    # ------------------------------------------------------------------
    def add_to_inventory(
        self, user_id: int, item_id: int, quantity: int = 1, durability: int = 100
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM items WHERE id = ?", (item_id,))
            if not cur.fetchone():
                raise ValueError("invalid item")
            cur.execute(
                """
                INSERT INTO user_items (user_id, item_id, quantity, durability)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = user_items.quantity + excluded.quantity
                """,
                (user_id, item_id, quantity, durability),
            )
            conn.commit()

    def remove_from_inventory(self, user_id: int, item_id: int, quantity: int = 1) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT quantity FROM user_items WHERE user_id = ? AND item_id = ?",
                (user_id, item_id),
            )
            row = cur.fetchone()
            if not row or row[0] < quantity:
                raise ValueError("not enough items")
            new_qty = row[0] - quantity
            if new_qty > 0:
                cur.execute(
                    "UPDATE user_items SET quantity = ? WHERE user_id = ? AND item_id = ?",
                    (new_qty, user_id, item_id),
                )
            else:
                cur.execute(
                    "DELETE FROM user_items WHERE user_id = ? AND item_id = ?",
                    (user_id, item_id),
                )
            conn.commit()

    def consume_drug(self, user_id: int, item_id: int) -> Dict[str, object]:
        """Consume a drug item and apply its effects."""

        item = self.get_item(item_id)
        if item.category != "drug":
            raise ValueError("not a drug")
        self.remove_from_inventory(user_id, item_id, 1)
        return addiction_service.update_addiction(user_id, item.name)

    def get_inventory(self, user_id: int) -> Dict[int, int]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT item_id, quantity FROM user_items WHERE user_id = ?",
                (user_id,),
            )
            return {r["item_id"]: r["quantity"] for r in cur.fetchall()}

    def get_inventory_item(self, user_id: int, item_id: int) -> Dict[str, int]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT quantity, durability FROM user_items WHERE user_id = ? AND item_id = ?",
                (user_id, item_id),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("item not in inventory")
            return {"quantity": row[0], "durability": row[1]}

    def repair_item(self, user_id: int, item_id: int, amount: int | None = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT durability FROM user_items WHERE user_id = ? AND item_id = ?",
                (user_id, item_id),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("item not in inventory")
            current = row[0]
            if amount is None:
                new_dur = 100
            else:
                new_dur = min(100, current + amount)
            cur.execute(
                "UPDATE user_items SET durability = ? WHERE user_id = ? AND item_id = ?",
                (new_dur, user_id, item_id),
            )
            conn.commit()
            return new_dur

    # helper for routes
    def asdict(self, item: Item) -> Dict:
        return asdict(item)


# default shared instance
item_service = ItemService()

__all__ = ["ItemService", "item_service"]

