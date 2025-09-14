from __future__ import annotations

"""Service layer for handling tutor-led training sessions."""

from typing import Dict, Optional

from models.tutor import Tutor
from models.skill import Skill
from models.learning_method import LearningMethod, METHOD_PROFILES
from backend.services.avatar_service import AvatarService
from backend.services.economy_service import EconomyService
from backend.services.skill_service import SkillService, skill_service


class TutorService:
    """Manage tutor definitions and paid training sessions."""

    def __init__(
        self,
        economy: Optional[EconomyService] = None,
        skills: Optional[SkillService] = None,
        avatar_service: AvatarService | None = None,
    ) -> None:
        self.economy = economy or EconomyService()
        # Ensure economy schema exists for tests/in-memory usage
        try:
            self.economy.ensure_schema()
        except Exception:
            pass
        self.skills = skills or skill_service
        self.avatar_service = avatar_service or AvatarService()
        self._tutors: Dict[int, Tutor] = {}
        self._id_seq = 1

    # ------------------------------------------------------------------
    # Tutor management
    def create_tutor(self, tutor: Tutor) -> Tutor:
        tutor.id = self._id_seq
        self._tutors[tutor.id] = tutor
        self._id_seq += 1
        return tutor

    def list_tutors(self) -> list[Tutor]:
        return list(self._tutors.values())

    # ------------------------------------------------------------------
    # Session logic
    def schedule_session(
        self, user_id: int, skill: Skill, tutor_id: int, hours: int
    ) -> dict:
        """Withdraw cost and grant XP for a tutor session."""

        tutor = self._tutors.get(tutor_id)
        if not tutor:
            raise ValueError("invalid tutor")
        if tutor.specialization != skill.name:
            raise ValueError("tutor does not teach this skill")

        inst = self.skills.train(user_id, skill, 0)
        profile = METHOD_PROFILES[LearningMethod.TUTOR]
        if inst.level < profile.min_level:
            raise ValueError("skill level too low for tutor")

        avatar = self.avatar_service.get_avatar(user_id)
        stamina = avatar.stamina if avatar else 50
        cost = tutor.hourly_rate * hours * (200 - stamina) // 100
        self.economy.withdraw(user_id, cost)

        before = inst.xp
        updated = self.skills.train_with_method(
            user_id, skill, LearningMethod.TUTOR, hours
        )
        gained = updated.xp - before
        xp_per_hour = gained // hours if hours else 0
        return {
            "status": "ok",
            "skill": updated,
            "xp_gained": gained,
            "xp_per_hour": xp_per_hour,
        }

    def highest_xp_per_hour(self) -> int:
        """Return the XP rate per hour for tutor sessions."""

        return METHOD_PROFILES[LearningMethod.TUTOR].xp_per_hour


# Shared instance
tutor_service = TutorService()

__all__ = ["TutorService", "tutor_service"]
