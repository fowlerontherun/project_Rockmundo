"""Service layer for managing XP modifying items."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from backend.models.xp_item import XPItem


class XPItemService:
    def __init__(self) -> None:
        self._items: Dict[int, XPItem] = {}
        self._inventories: Dict[int, List[int]] = {}
        self._active_boosts: Dict[int, List[Tuple[float, datetime]]] = {}
        self._id_seq = 1

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def list_items(self) -> List[XPItem]:
        return list(self._items.values())

    def create_item(self, item: XPItem) -> XPItem:
        item.id = self._id_seq
        self._items[item.id] = item
        self._id_seq += 1
        return item

    def update_item(self, item_id: int, **changes) -> XPItem:
        itm = self._items.get(item_id)
        if not itm:
            raise ValueError("Item not found")
        for k, v in changes.items():
            if hasattr(itm, k) and v is not None:
                setattr(itm, k, v)
        return itm

    def delete_item(self, item_id: int) -> None:
        if item_id in self._items:
            del self._items[item_id]

    # ------------------------------------------------------------------
    # Inventory management
    # ------------------------------------------------------------------
    def assign_to_user(self, user_id: int, item_id: int) -> None:
        if item_id not in self._items:
            raise ValueError("invalid item")
        self._inventories.setdefault(user_id, []).append(item_id)

    def _pop_from_inventory(self, user_id: int, item_id: int) -> XPItem:
        inv = self._inventories.get(user_id, [])
        if item_id not in inv:
            raise ValueError("item not in inventory")
        inv.remove(item_id)
        return self._items[item_id]

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


xp_item_service = XPItemService()

__all__ = ["XPItemService", "xp_item_service"]
