"""Service for managing perk unlocks based on attributes and skills."""

from __future__ import annotations

from typing import Dict, List, Set

from models.perk import Perk


class PerkService:
    """Track perks unlocked by users and evaluate requirements."""

    def __init__(self) -> None:
        # Registered perk definitions
        self._perks: Dict[int, Perk] = {}
        # Map of user -> set of perk ids granted
        self._granted: Dict[int, Set[int]] = {}
        # Track user attribute levels
        self._attributes: Dict[int, Dict[str, int]] = {}
        # Track user skill levels
        self._skills: Dict[int, Dict[str, int]] = {}

    # ------------------------------------------------------------------
    # Registration and queries
    def register_perk(self, perk: Perk) -> None:
        self._perks[perk.id] = perk

    def get_perks(self, user_id: int) -> List[Perk]:
        ids = self._granted.get(user_id, set())
        return [self._perks[i] for i in ids]

    # ------------------------------------------------------------------
    # State updates
    def update_attribute(self, user_id: int, stat: str, level: int) -> None:
        self._attributes.setdefault(user_id, {})[stat] = level
        self._evaluate(user_id)

    def update_skill(self, user_id: int, skill: str, level: int) -> None:
        self._skills.setdefault(user_id, {})[skill] = level
        self._evaluate(user_id)

    # ------------------------------------------------------------------
    def _evaluate(self, user_id: int) -> None:
        granted = self._granted.setdefault(user_id, set())
        attrs = self._attributes.get(user_id, {})
        skills = self._skills.get(user_id, {})
        for perk in self._perks.values():
            if perk.id in granted:
                continue
            meets = True
            for name, lvl in perk.requirements.items():
                level = attrs.get(name)
                if level is None:
                    level = skills.get(name)
                if level is None or level < lvl:
                    meets = False
                    break
            if meets:
                granted.add(perk.id)

    # ------------------------------------------------------------------
    def reset(self) -> None:
        """Clear all stored state (useful for tests)."""

        self._perks.clear()
        self._granted.clear()
        self._attributes.clear()
        self._skills.clear()


perk_service = PerkService()

__all__ = ["PerkService", "perk_service"]
