"""Service layer for managing XP modifying items backed by SQLite."""
from __future__ import annotations
"""Service layer for managing XP modifying items backed by SQLite."""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

from backend.models.xp_item import XPItem


DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class XPItemService:
    """Persistence-backed XP item management and user inventories."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()
        self._active_boosts: Dict[int, List[Tuple[float, datetime]]] = {}

    # ------------------------------------------------------------------
    # schema helpers
    # ------------------------------------------------------------------
    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS xp_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    effect_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    duration INTEGER NOT NULL
                )
                """,
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_xp_items (
                    user_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    PRIMARY KEY (user_id, item_id),
                    FOREIGN KEY (item_id) REFERENCES xp_items(id)
                )
                """,
            )
            conn.commit()

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def _row_to_item(self, row: sqlite3.Row) -> XPItem:
        return XPItem(**dict(row))

    def list_items(self) -> List[XPItem]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT id, name, effect_type, amount, duration FROM xp_items")
            return [self._row_to_item(r) for r in cur.fetchall()]

    def create_item(self, item: XPItem) -> XPItem:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO xp_items (name, effect_type, amount, duration)
                VALUES (?, ?, ?, ?)
                """,
                (item.name, item.effect_type, item.amount, item.duration),
            )
            item.id = int(cur.lastrowid or 0)
            conn.commit()
        return item

    def _get_item(self, item_id: int) -> XPItem:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, name, effect_type, amount, duration FROM xp_items WHERE id = ?",
                (item_id,),
            )
            row = cur.fetchone()
        if not row:
            raise ValueError("Item not found")
        return self._row_to_item(row)

    def update_item(self, item_id: int, **changes) -> XPItem:
        if not changes:
            return self._get_item(item_id)
        updates = {k: v for k, v in changes.items() if v is not None}
        if not updates:
            return self._get_item(item_id)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        params = list(updates.values()) + [item_id]
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                f"UPDATE xp_items SET {set_clause} WHERE id = ?",
                params,
            )
            if cur.rowcount == 0:
                raise ValueError("Item not found")
            conn.commit()
        return self._get_item(item_id)

    def delete_item(self, item_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM xp_items WHERE id = ?", (item_id,))
            cur.execute("DELETE FROM user_xp_items WHERE item_id = ?", (item_id,))
            conn.commit()

    # ------------------------------------------------------------------
    # Inventory management
    # ------------------------------------------------------------------
    def assign_to_user(self, user_id: int, item_id: int) -> None:
        # ensure item exists
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM xp_items WHERE id = ?", (item_id,))
            if not cur.fetchone():
                raise ValueError("invalid item")
            cur.execute(
                """
                INSERT INTO user_xp_items (user_id, item_id, quantity)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + 1
                """,
                (user_id, item_id),
            )
            conn.commit()

    def _pop_from_inventory(self, user_id: int, item_id: int) -> XPItem:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT quantity FROM user_xp_items WHERE user_id = ? AND item_id = ?",
                (user_id, item_id),
            )
            row = cur.fetchone()
            if not row or row[0] <= 0:
                raise ValueError("item not in inventory")
            new_qty = row[0] - 1
            if new_qty > 0:
                cur.execute(
                    "UPDATE user_xp_items SET quantity = ? WHERE user_id = ? AND item_id = ?",
                    (new_qty, user_id, item_id),
                )
            else:
                cur.execute(
                    "DELETE FROM user_xp_items WHERE user_id = ? AND item_id = ?",
                    (user_id, item_id),
                )
            conn.commit()
        return self._get_item(item_id)

    # ------------------------------------------------------------------
    # Effect application
    # ------------------------------------------------------------------
    def apply_item(self, user_id: int, item_id: int) -> float:
        item = self._pop_from_inventory(user_id, item_id)
        if item.effect_type == "flat":
            return item.amount
        expires = datetime.utcnow() + timedelta(seconds=item.duration)
        self._active_boosts.setdefault(user_id, []).append((item.amount, expires))
        return 0.0

    def get_active_multiplier(self, user_id: int) -> float:
        now = datetime.utcnow()
        boosts = self._active_boosts.get(user_id, [])
        active: List[Tuple[float, datetime]] = []
        mult = 1.0
        for amt, exp in boosts:
            if exp > now:
                mult *= amt
                active.append((amt, exp))
        self._active_boosts[user_id] = active
        return mult


# default shared instance
xp_item_service = XPItemService()

__all__ = ["XPItemService", "xp_item_service"]

