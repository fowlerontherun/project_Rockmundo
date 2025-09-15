"""Service managing gear crafting and bonuses."""
from __future__ import annotations

import random
from dataclasses import asdict
from itertools import chain
from typing import Dict, List

from models.gear import BaseItem, GearComponent, GearItem, StatModifier


class GearService:
    """In-memory gear crafting and management."""

    def __init__(self) -> None:
        self.base_items: Dict[str, BaseItem] = {}
        self.components: Dict[str, GearComponent] = {}
        self.items: Dict[int, GearItem] = {}
        self._ownership: Dict[int, int] = {}  # item_id -> band_id
        self._band_items: Dict[int, List[int]] = {}
        self._id_seq = 1

    # ------------------------------------------------------------------
    # crafting and upgrades
    # ------------------------------------------------------------------
    def craft(self, base_name: str, component_names: List[str]) -> GearItem | None:
        base = self.base_items.get(base_name)
        if not base:
            raise ValueError("unknown base item")
        comps: List[GearComponent] = []
        chance = 1.0
        for name in component_names:
            comp = self.components.get(name)
            if not comp:
                raise ValueError(f"unknown component {name}")
            comps.append(comp)
            chance *= comp.success_rate
        if random.random() > chance:
            return None
        durability = base.durability + sum(c.durability_bonus for c in comps)
        modifiers = list(base.base_modifiers) + list(chain.from_iterable(c.modifiers for c in comps))
        item = GearItem(id=self._id_seq, name=base.name, durability=durability, modifiers=modifiers)
        self.items[item.id] = item
        self._id_seq += 1
        return item

    def upgrade(self, item_id: int, component_name: str) -> GearItem | None:
        item = self.items.get(item_id)
        comp = self.components.get(component_name)
        if not item or not comp:
            raise ValueError("invalid item or component")
        if random.random() > comp.success_rate:
            item.durability = max(0, item.durability - 5)
            return None
        item.durability += comp.durability_bonus
        item.modifiers.extend(comp.modifiers)
        return item

    def repair(self, item_id: int, amount: int) -> GearItem:
        item = self.items[item_id]
        item.durability += amount
        return item

    # ------------------------------------------------------------------
    # ownership and bonuses
    # ------------------------------------------------------------------
    def assign_to_band(self, band_id: int, item: GearItem) -> None:
        self._ownership[item.id] = band_id
        self._band_items.setdefault(band_id, []).append(item.id)

    def trade(self, item_id: int, from_band: int, to_band: int) -> None:
        owner = self._ownership.get(item_id)
        if owner != from_band:
            raise ValueError("item not owned by source band")
        self._ownership[item_id] = to_band
        self._band_items[from_band].remove(item_id)
        self._band_items.setdefault(to_band, []).append(item_id)

    def get_band_bonus(self, band_id: int, stat: str) -> float:
        total = 0.0
        for iid in self._band_items.get(band_id, []):
            item = self.items[iid]
            for mod in item.modifiers:
                if mod.stat == stat:
                    total += mod.amount
        return total

    # helper for routes
    def asdict(self, item: GearItem) -> Dict:
        data = asdict(item)
        data["modifiers"] = [asdict(m) for m in item.modifiers]
        return data


gear_service = GearService()

__all__ = ["GearService", "gear_service"]
