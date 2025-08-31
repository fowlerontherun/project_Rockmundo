"""Service layer for managing skill progression.

The service keeps an in-memory record of a user's skills while
coordinating XP modifiers from lifestyle effects and global XP events.
It is intentionally lightweight – perfect for unit testing and small
demo environments.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Dict, Tuple

from backend.database import DB_PATH
from backend.models.skill import Skill
from backend.models.xp_config import get_config
from backend.services.xp_event_service import XPEventService


SONGWRITING_SKILL = Skill(id=4, name="songwriting", category="creative")


class SkillService:
    """Track and mutate skill progression for users."""

    def __init__(
        self,
        xp_events: XPEventService | None = None,
        db_path: Path | None = None,
    ) -> None:
        self.xp_events = xp_events or XPEventService()
        self.db_path = db_path or DB_PATH
        # Keyed by (user_id, skill_id)
        self._skills: Dict[Tuple[int, int], Skill] = {}
        # Track XP earned per day to enforce caps
        self._xp_today: Dict[Tuple[int, int, date], int] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    def _lifestyle_modifier(self, user_id: int) -> float:
        """Return the last lifestyle XP modifier for the user."""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT modifier FROM xp_modifiers WHERE user_id = ? ORDER BY date DESC LIMIT 1",
                    (user_id,),
                )
                row = cur.fetchone()
        except sqlite3.Error:
            row = None
        return row[0] if row else 1.0

    def _get_skill(self, user_id: int, skill: Skill) -> Skill:
        key = (user_id, skill.id)
        if key not in self._skills:
            self._skills[key] = Skill(
                id=skill.id,
                name=skill.name,
                category=skill.category,
                parent_id=skill.parent_id,
            )
        return self._skills[key]

    def _check_level(self, skill: Skill) -> None:
        level = skill.xp // 100 + 1
        if level != skill.level:
            skill.level = level

    # ------------------------------------------------------------------
    # Public API
    def train(self, user_id: int, skill: Skill, base_xp: int) -> Skill:
        """Apply training XP to a skill respecting modifiers and caps."""

        inst = self._get_skill(user_id, skill)

        modifier = self._lifestyle_modifier(user_id)
        modifier *= self.xp_events.get_active_multiplier(skill.name)

        gain = int(base_xp * modifier)

        today = date.today()
        cap = get_config().daily_cap
        if cap:
            used = self._xp_today.get((user_id, skill.id, today), 0)
            allowed = max(0, cap - used)
            if gain > allowed:
                gain = allowed
            self._xp_today[(user_id, skill.id, today)] = used + gain

        inst.xp += gain
        self._check_level(inst)
        return inst

    def apply_decay(self, user_id: int, skill_id: int, amount: int) -> Skill | None:
        """Reduce XP for a skill and update its level."""

        inst = self._skills.get((user_id, skill_id))
        if not inst:
            return None
        inst.xp = max(0, inst.xp - amount)
        self._check_level(inst)
        return inst

    def apply_daily_decay(self, user_id: int, amount: int = 1) -> None:
        """Apply decay to all tracked skills for a user."""

        for (uid, _sid), skill in list(self._skills.items()):
            if uid == user_id:
                self.apply_decay(uid, skill.id, amount)

    def decay_all(self, amount: int = 1) -> None:
        """Global decay across all users (scheduler hook)."""

        for (uid, sid) in list(self._skills.keys()):
            self.apply_decay(uid, sid, amount)

    # ------------------------------------------------------------------
    # Songwriting helpers
    def get_songwriting_skill(self, user_id: int) -> Skill:
        """Return the songwriting skill instance for the user."""

        return self._get_skill(user_id, SONGWRITING_SKILL)

    def add_songwriting_xp(self, user_id: int, revised: bool = False) -> Skill:
        """Award XP for songwriting actions."""

        base = 5 if revised else 10
        return self.train(user_id, SONGWRITING_SKILL, base)


skill_service = SkillService()

__all__ = ["SkillService", "skill_service", "SONGWRITING_SKILL"]

