from __future__ import annotations

"""Service layer providing training for image-related skills."""

from typing import Dict

from backend.models.skill import Skill
from backend.seeds.skill_seed import SKILL_NAME_TO_ID
from services.skill_service import SkillService
from services.skill_service import skill_service as default_skill_service


class ImageTrainingService:
    """Offer workshops and courses for image skills."""

    def __init__(
        self,
        svc: SkillService | None = None,
        skill_service: SkillService | None = None,
    ) -> None:
        """Create a training service using the provided skill service.

        The ``skill_service`` keyword is kept for backward compatibility.
        """

        self.skill_service = svc or skill_service or default_skill_service
        self._workshop_xp: Dict[str, int] = {"fashion": 40}
        self._course_xp: Dict[str, int] = {"image_management": 100}

    def attend_workshop(self, user_id: int, skill_name: str) -> Skill:
        """Attend a workshop for the given skill and gain XP."""

        if skill_name not in self._workshop_xp:
            raise ValueError("unknown_workshop")
        skill_id = SKILL_NAME_TO_ID[skill_name]
        skill = Skill(id=skill_id, name=skill_name, category="image")
        return self.skill_service.train(
            user_id, skill, self._workshop_xp[skill_name]
        )

    def attend_course(self, user_id: int, skill_name: str) -> Skill:
        """Complete a course for the given skill and gain XP."""

        if skill_name not in self._course_xp:
            raise ValueError("unknown_course")
        skill_id = SKILL_NAME_TO_ID[skill_name]
        skill = Skill(id=skill_id, name=skill_name, category="image")
        return self.skill_service.train(
            user_id, skill, self._course_xp[skill_name]
        )


# Default shared instance
image_training_service = ImageTrainingService()

__all__ = ["ImageTrainingService", "image_training_service"]

