"""Service layer for generic items and inventories."""
from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

from backend.models.item import Item, ItemCategory


class ItemService:
    """In-memory management of items and inventories."""

    def __init__(self) -> None:
        self._items: Dict[int, Item] = {}
        self._categories: Dict[str, ItemCategory] = {}
        self._inventories: Dict[int, Dict[int, int]] = {}
        self._id_seq = 1

    # ------------------------------------------------------------------
    # Category operations
    # ------------------------------------------------------------------
    def list_categories(self) -> List[ItemCategory]:
        return list(self._categories.values())

    def create_category(self, category: ItemCategory) -> ItemCategory:
        self._categories[category.name] = category
        return category

    def delete_category(self, name: str) -> None:
        self._categories.pop(name, None)

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def list_items(self) -> List[Item]:
        return list(self._items.values())

    def create_item(self, item: Item) -> Item:
        item.id = self._id_seq
        self._items[item.id] = item
        self._id_seq += 1
        return item

    def update_item(self, item_id: int, **changes) -> Item:
        itm = self._items.get(item_id)
        if not itm:
            raise ValueError("Item not found")
        for k, v in changes.items():
            if hasattr(itm, k) and v is not None:
                setattr(itm, k, v)
        return itm

    def delete_item(self, item_id: int) -> None:
        self._items.pop(item_id, None)
        for inv in self._inventories.values():
            inv.pop(item_id, None)

    # ------------------------------------------------------------------
    # Inventory management
    # ------------------------------------------------------------------
    def add_to_inventory(self, user_id: int, item_id: int, quantity: int = 1) -> None:
        if item_id not in self._items:
            raise ValueError("invalid item")
        inv = self._inventories.setdefault(user_id, {})
        inv[item_id] = inv.get(item_id, 0) + quantity

    def remove_from_inventory(self, user_id: int, item_id: int, quantity: int = 1) -> None:
        inv = self._inventories.get(user_id, {})
        if inv.get(item_id, 0) < quantity:
            raise ValueError("not enough items")
        inv[item_id] -= quantity
        if inv[item_id] <= 0:
            del inv[item_id]

    def get_inventory(self, user_id: int) -> Dict[int, int]:
        return dict(self._inventories.get(user_id, {}))

    # helper for routes
    def asdict(self, item: Item) -> Dict:
        return asdict(item)


item_service = ItemService()

__all__ = ["ItemService", "item_service"]
