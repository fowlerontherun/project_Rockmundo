"""Service layer for managing skill progression.

The service keeps an in-memory record of a user's skills while
coordinating XP modifiers from lifestyle effects and global XP events.
It is intentionally lightweight – perfect for unit testing and small
demo environments.
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date
from pathlib import Path
from typing import Dict, Tuple

from backend.database import DB_PATH
from backend.models.book import Book
from backend.models.learning_method import METHOD_PROFILES, LearningMethod
from backend.models.learning_style import LEARNING_STYLE_BONUS, LearningStyle
from backend.models.skill import Skill
from backend.models.xp_config import get_config
from backend.services.item_service import item_service
from backend.services.lifestyle_scheduler import lifestyle_xp_modifier
from backend.services.xp_event_service import XPEventService
from backend.services.avatar_service import AvatarService
from backend.schemas.avatar import AvatarUpdate
from backend.services.xp_item_service import xp_item_service

INTERNET_DEVICE_NAME = "internet device"


SONGWRITING_SKILL = Skill(id=4, name="songwriting", category="creative")


class SkillService:
    """Track and mutate skill progression for users."""

    def __init__(
        self,
        xp_events: XPEventService | None = None,
        db_path: Path | None = None,
        avatar_service: AvatarService | None = None,
    ) -> None:
        self.xp_events = xp_events or XPEventService()
        self.db_path = db_path or DB_PATH
        self.avatar_service = avatar_service or AvatarService()
        # Keyed by (user_id, skill_id)
        self._skills: Dict[Tuple[int, int], Skill] = {}
        # Track XP earned per day to enforce caps
        self._xp_today: Dict[Tuple[int, int, date], int] = {}
        # Track consecutive method usage for burnout
        self._method_history: Dict[int, Tuple[LearningMethod | None, int]] = {}
        # Temporary XP buffs awarded for session successes
        # key -> (multiplier, remaining_uses)
        self._session_buffs: Dict[Tuple[int, int], Tuple[float, int]] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    def _lifestyle_modifier(self, user_id: int) -> float:
        """Combine lifestyle metrics and stored modifiers for XP."""

        modifier = 1.0
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                # Lifestyle metrics
                cur.execute(
                    "SELECT sleep_hours, stress, training_discipline, mental_health, nutrition, fitness FROM lifestyle WHERE user_id = ?",
                    (user_id,),
                )
                row = cur.fetchone()
                if row:
                    modifier *= lifestyle_xp_modifier(*row)
                # Stored modifiers (e.g., events)
                cur.execute(
                    "SELECT modifier FROM xp_modifiers WHERE user_id = ? ORDER BY date DESC LIMIT 1",
                    (user_id,),
                )
                row = cur.fetchone()
                if row:
                    modifier *= row[0]
        except sqlite3.Error:
            pass
        return modifier

    def _learning_style(self, user_id: int) -> LearningStyle:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT learning_style FROM users WHERE id = ?",
                    (user_id,),
                )
                row = cur.fetchone()
        except sqlite3.Error:
            row = None
        try:
            return LearningStyle(row[0]) if row and row[0] else LearningStyle.BALANCED
        except ValueError:
            return LearningStyle.BALANCED

    def _get_skill(self, user_id: int, skill: Skill) -> Skill:
        key = (user_id, skill.id)
        if key not in self._skills:
            self._skills[key] = Skill(
                id=skill.id,
                name=skill.name,
                category=skill.category,
                parent_id=skill.parent_id,
                specializations=skill.specializations,
                prerequisites=skill.prerequisites,
            )
        else:
            if skill.specializations:
                self._skills[key].specializations = skill.specializations
            if skill.prerequisites:
                self._skills[key].prerequisites = skill.prerequisites
        return self._skills[key]

    def _synergy_bonus(self, user_id: int, skill: Skill) -> float:
        """Return XP multiplier from specialization synergies."""

        spec_name = skill.specialization
        if not spec_name:
            return 1.0
        spec = skill.specializations.get(spec_name)
        if not spec:
            return 1.0
        bonus = 1.0
        for related_id, threshold in spec.related_skills.items():
            other = self._skills.get((user_id, related_id))
            if other and other.level >= threshold:
                bonus += spec.bonus
        return bonus

    def select_specialization(
        self, user_id: int, skill: Skill, specialization: str
    ) -> Skill:
        """Select a specialization for a user's skill."""

        inst = self._get_skill(user_id, skill)
        inst.specialization = specialization
        if skill.specializations:
            inst.specializations = skill.specializations
        return inst

    def _check_level(self, skill: Skill) -> None:
        level = skill.xp // 100 + 1
        cap = get_config().level_cap
        if cap:
            level = min(level, cap)
        if level != skill.level:
            skill.level = level

    def _has_item(self, user_id: int, item_name: str) -> bool:
        """Return True if the user possesses an item by name."""

        inv = item_service.get_inventory(user_id)
        for item in item_service.list_items():
            if item.name == item_name:
                return inv.get(item.id, 0) > 0
        return False

    # ------------------------------------------------------------------
    # Public API
    def train(self, user_id: int, skill: Skill, base_xp: int) -> Skill:
        """Apply training XP to a skill respecting modifiers and caps."""

        inst = self._get_skill(user_id, skill)

        modifier = self._lifestyle_modifier(user_id)
        modifier *= self.xp_events.get_active_multiplier(skill.name)
        item_mult = xp_item_service.get_active_multiplier(user_id)
        modifier *= item_mult

        buff_mult = 1.0
        key = (user_id, skill.id)
        buff = self._session_buffs.get(key)
        if buff:
            buff_mult = buff[0]
            remaining = buff[1] - 1
            if remaining <= 0:
                self._session_buffs.pop(key, None)
            else:
                self._session_buffs[key] = (buff[0], remaining)

        gain = int(base_xp * modifier * buff_mult * self._synergy_bonus(user_id, inst))
        avatar = self.avatar_service.get_avatar(user_id)

        if avatar:
            attr_map = {
                "creative": avatar.creativity,
                "performance": avatar.charisma,
                "stage": avatar.charisma,
                "business": avatar.intelligence,
            }
            attr_val = attr_map.get(inst.category)
            if attr_val is not None:
                gain = int(gain * (1 + attr_val / 200))
            discipline = avatar.discipline
        else:
            discipline = 50

        gain = int(gain * (1 + (discipline - 50) / 100))

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

    def train_with_method(
        self,
        user_id: int,
        skill: Skill,
        method: LearningMethod,
        duration: int,
        book: Book | None = None,
        environment_quality: float = 1.0,
    ) -> Skill:
        """Train a skill using a specific learning method.

        The method defines XP and cost rates along with level restrictions.
        """
        profile = METHOD_PROFILES[method]

        # Ensure prerequisite skills are met before training
        for prereq_id, required in skill.prerequisites.items():
            prereq = self._skills.get((user_id, prereq_id))
            if not prereq or prereq.level < required:
                raise ValueError("missing prerequisite skills")

        inst = self._get_skill(user_id, skill)

        if method == LearningMethod.YOUTUBE and not self._has_item(
            user_id, INTERNET_DEVICE_NAME
        ):
            raise ValueError("internet device required for this method")

        # Level gating
        if inst.level < profile.min_level:
            raise ValueError("skill level too low for this method")
        if profile.max_level and inst.level > profile.max_level:
            raise ValueError("skill level too high for this method")

        if method == LearningMethod.BOOK and book is not None:
            if inst.level >= book.max_skill_level:
                return inst
            xp_rate = int(profile.xp_per_hour * 0.5)
            base_xp = xp_rate * duration
            max_xp_total = book.max_skill_level * 100 - 1
            allowed = max_xp_total - inst.xp
            if allowed <= 0:
                return inst
            base_xp = min(base_xp, allowed)
        else:
            base_xp = profile.xp_per_hour * duration

        if profile.session_cap:
            base_xp = min(base_xp, profile.session_cap)

        if random.random() < 0.05:
            base_xp *= 2

        # Environment quality bonus
        base_xp *= environment_quality

        # Learning style influence
        style = self._learning_style(user_id)
        base_xp *= LEARNING_STYLE_BONUS.get(style, {}).get(method, 1.0)

        # Burnout diminishing returns
        last, streak = self._method_history.get(user_id, (None, 0))
        if last == method:
            streak += 1
        else:
            streak = 1
        burnout = 0.9 ** (streak - 1)
        base_xp *= burnout
        self._method_history[user_id] = (method, streak)

        result = self.train(user_id, skill, int(base_xp))

        # Training consumes stamina based on session duration.
        avatar = self.avatar_service.get_avatar(user_id)
        if avatar:
            cost = duration // 2
            cost = int(cost * (1.5 - avatar.discipline / 100))
            new_stamina = max(0, avatar.stamina - cost)
            self.avatar_service.update_avatar(
                user_id, AvatarUpdate(stamina=new_stamina)
            )

        return result

    def reduce_burnout(self, user_id: int, amount: int = 1) -> None:
        """Reduce the stored burnout streak for a user.

        A streak of repetitive learning methods causes diminishing returns.
        Recovery actions can call this to lower the streak and ease the XP
        penalty.

        Parameters
        ----------
        user_id: int
            The user whose streak should be reduced.
        amount: int
            How much to reduce the streak by. If the streak drops to zero the
            history entry is cleared.
        """

        last, streak = self._method_history.get(user_id, (None, 0))
        if streak <= 0:
            return
        streak = max(0, streak - amount)
        if streak == 0:
            self._method_history.pop(user_id, None)
        else:
            self._method_history[user_id] = (last, streak)

    def apply_decay(self, user_id: int, skill_id: int, amount: int) -> Skill | None:
        """Reduce XP for a skill and update its level."""

        inst = self._skills.get((user_id, skill_id))
        if not inst:
            return None
        inst.xp = max(0, inst.xp - amount)
        self._check_level(inst)
        return inst

    def decay_skills(self, user_id: int, amount: int) -> None:
        """Apply decay to skills scaled by the avatar's discipline."""

        avatar = self.avatar_service.get_avatar(user_id)
        factor = 1.0
        if avatar:
            factor = 1 - avatar.discipline / 200
        decay = int(amount * factor)
        for (uid, _sid), skill in list(self._skills.items()):
            if uid == user_id:
                self.apply_decay(uid, skill.id, decay)

    def apply_daily_decay(self, user_id: int, amount: int = 1) -> None:
        """Apply decay to all tracked skills for a user."""
        avatar = self.avatar_service.get_avatar(user_id)
        factor = 1.0
        if avatar:
            factor += max(0, 50 - avatar.stamina) / 50
        decay = int(amount * factor)
        self.decay_skills(user_id, decay)

    def decay_all(self, amount: int = 1) -> None:
        """Global decay across all users (scheduler hook)."""
        users = {uid for (uid, _sid) in self._skills.keys()}
        for uid in users:
            self.apply_daily_decay(uid, amount)

    # ------------------------------------------------------------------
    # Songwriting helpers
    def get_songwriting_skill(self, user_id: int) -> Skill:
        """Return the songwriting skill instance for the user."""

        return self._get_skill(user_id, SONGWRITING_SKILL)

    def add_songwriting_xp(self, user_id: int, revised: bool = False) -> Skill:
        """Award XP for songwriting actions."""

        base = 5 if revised else 10
        return self.train(user_id, SONGWRITING_SKILL, base)

    def grant_temp_buff(
        self, user_id: int, skill: Skill, multiplier: float = 1.2, uses: int = 1
    ) -> None:
        """Grant a temporary XP multiplier for the next training sessions."""

        if multiplier <= 1.0 or uses <= 0:
            return
        self._session_buffs[(user_id, skill.id)] = (multiplier, uses)

    def reward_songwriting_session(
        self, user_id: int, multiplier: float = 1.2, uses: int = 1
    ) -> None:
        """Convenience wrapper to reward songwriting successes with a buff."""

        self.grant_temp_buff(user_id, SONGWRITING_SKILL, multiplier, uses)


skill_service = SkillService()

__all__ = ["SkillService", "skill_service", "SONGWRITING_SKILL"]

