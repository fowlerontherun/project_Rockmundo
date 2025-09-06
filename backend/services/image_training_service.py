"""Training helpers for image and style related skills."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from backend.models.skill import Skill
from backend.models.learning_method import LearningMethod
from backend.services.economy_service import EconomyService
from backend.services.skill_service import skill_service


# ---------------------------------------------------------------------------
# Online tutorials
# ---------------------------------------------------------------------------

def study_image_tutorial(user_id: int, skill: Skill, hours: int) -> Skill:
    """Train an image related skill via online tutorials."""
    return skill_service.train_with_method(
        user_id, skill, LearningMethod.YOUTUBE, hours
    )


# ---------------------------------------------------------------------------
# Stylist NPC training
# ---------------------------------------------------------------------------


@dataclass
class Stylist:
    id: int | None
    name: str
    specialization: str
    hourly_rate: int


class StylistService:
    """Simple service for hiring stylists to train image skills."""

    def __init__(
        self,
        economy: Optional[EconomyService] = None,
        skills=skill_service,
    ) -> None:
        self.economy = economy or EconomyService()
        self.skills = skills
        self._stylists: Dict[int, Stylist] = {}
        self._id_seq = 1

    def create_stylist(self, stylist: Stylist) -> Stylist:
        stylist.id = self._id_seq
        self._stylists[stylist.id] = stylist
        self._id_seq += 1
        return stylist

    def list_stylists(self) -> list[Stylist]:
        return list(self._stylists.values())

    def schedule_session(
        self, user_id: int, skill: Skill, stylist_id: int, hours: int
    ) -> dict:
        stylist = self._stylists.get(stylist_id)
        if not stylist or stylist.specialization != skill.name:
            raise ValueError("invalid stylist")
        cost = stylist.hourly_rate * hours
        self.economy.withdraw(user_id, cost)
        before = self.skills.train(user_id, skill, 0).xp
        updated = self.skills.train_with_method(
            user_id, skill, LearningMethod.TUTOR, hours
        )
        gained = updated.xp - before
        return {"status": "ok", "skill": updated, "xp_gained": gained}


stylist_service = StylistService()

__all__ = [
    "study_image_tutorial",
    "Stylist",
    "StylistService",
    "stylist_service",
]
