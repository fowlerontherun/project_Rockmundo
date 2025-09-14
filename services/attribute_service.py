"""Service for managing user attributes."""

from __future__ import annotations

from typing import Dict, Tuple

from models.attribute import Attribute
from backend.services.perk_service import perk_service
from backend.models.attribute import Attribute
from services.perk_service import perk_service


class AttributeService:
    """Track and train attributes for users."""

    def __init__(self) -> None:
        # keyed by (user_id, stat)
        self._attributes: Dict[Tuple[int, str], Attribute] = {}

    def _get(self, user_id: int, stat: str) -> Attribute:
        key = (user_id, stat)
        if key not in self._attributes:
            self._attributes[key] = Attribute(stat=stat)
        return self._attributes[key]

    def get_attribute(self, user_id: int, stat: str) -> Attribute:
        """Return a user's attribute, creating if necessary."""

        return self._get(user_id, stat)

    def train_attribute(self, user_id: int, stat: str, amount: int) -> Attribute:
        """Increment XP for a stat and update its level.

        Stamina reduces the effective training cost for other stats by its
        current level.
        """

        attr = self._get(user_id, stat)
        stamina_level = self._get(user_id, "stamina").level
        reduction = stamina_level if stat != "stamina" else 0
        gained = max(1, amount - reduction)
        attr.xp += gained
        attr.level = attr.xp // 100 + 1
        # Evaluate perk requirements after level change
        perk_service.update_attribute(user_id, stat, attr.level)
        return attr


attribute_service = AttributeService()
