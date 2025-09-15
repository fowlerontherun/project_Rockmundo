from __future__ import annotations

from backend.models.skill import Skill
from seeds.skill_seed import SKILL_NAME_TO_ID
from backend.services.skill_service import SkillService
from backend.services.skill_service import skill_service as default_skill_service


class SocialMediaTrainingService:
    """Provide workshops for social media management skills."""

    def __init__(self, skill_service: SkillService | None = None) -> None:
        self.skill_service = skill_service or default_skill_service
        self._workshop_xp = {"social_media_management": 50}

    def attend_workshop(self, user_id: int, skill_name: str = "social_media_management") -> Skill:
        """Attend a workshop to gain XP in social media management."""
        if skill_name not in self._workshop_xp:
            raise ValueError("unknown_workshop")
        skill_id = SKILL_NAME_TO_ID[skill_name]
        skill = Skill(id=skill_id, name=skill_name, category="business")
        return self.skill_service.train(
            user_id, skill, self._workshop_xp[skill_name]
        )


# Default shared instance
social_media_training_service = SocialMediaTrainingService()

__all__ = ["SocialMediaTrainingService", "social_media_training_service"]

