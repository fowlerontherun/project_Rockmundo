"""Service layer providing training for vocal-related skills."""

from __future__ import annotations

from models.learning_method import LearningMethod
from models.skill import Skill
from backend.seeds.skill_seed import SEED_SKILLS
from services.skill_service import SkillService
from services.skill_service import skill_service as default_skill_service


class VocalTrainingService:
    """Offer practice sessions for vocal sub-skills."""

    _trainable = {
        "breath_control",
        "vibrato_control",
        "harmonization",
        "falsetto",
        "screaming",
    }

    def __init__(self, svc: SkillService | None = None) -> None:
        self.skill_service = svc or default_skill_service
        self._seed_map = {skill.name: skill for skill in SEED_SKILLS}

    def practice(self, user_id: int, skill_name: str, hours: int) -> Skill:
        """Practice a vocal skill for a number of hours."""

        if skill_name not in self._trainable:
            raise ValueError("unknown_vocal_skill")
        template = self._seed_map[skill_name]
        skill = Skill(
            id=template.id,
            name=template.name,
            category=template.category,
            parent_id=template.parent_id,
            prerequisites=template.prerequisites,
        )
        return self.skill_service.train_with_method(
            user_id, skill, LearningMethod.PRACTICE, hours
        )


vocal_training_service = VocalTrainingService()

__all__ = ["VocalTrainingService", "vocal_training_service"]
