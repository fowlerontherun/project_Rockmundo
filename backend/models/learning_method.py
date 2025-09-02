from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class LearningMethod(str, Enum):
    """Different approaches for learning a skill."""

    BOOK = "book"
    UNIVERSITY = "university"
    APPRENTICESHIP = "apprenticeship"
    YOUTUBE = "youtube"
    TUTOR = "tutor"
    BANDMATE = "bandmate"
    WORKSHOP = "workshop"
    PRACTICE = "practice"


@dataclass(frozen=True)
class MethodProfile:
    """Configuration for a learning method.

    Attributes:
        xp_per_hour: Base XP earned per hour.
        cost_per_hour: Monetary cost per hour.
        session_cap: Optional maximum XP awarded per session.
        min_level: Minimum skill level required to use the method.
        max_level: Optional maximum skill level after which the method is no longer effective.
    """

    xp_per_hour: int
    cost_per_hour: int
    session_cap: int | None = None
    min_level: int = 1
    max_level: int | None = None


METHOD_PROFILES: Dict[LearningMethod, MethodProfile] = {
    LearningMethod.BOOK: MethodProfile(xp_per_hour=20, cost_per_hour=10, max_level=20),
    LearningMethod.UNIVERSITY: MethodProfile(xp_per_hour=40, cost_per_hour=100, min_level=20),
    LearningMethod.APPRENTICESHIP: MethodProfile(
        xp_per_hour=30, cost_per_hour=50, min_level=10
    ),
    LearningMethod.YOUTUBE: MethodProfile(
        xp_per_hour=15, cost_per_hour=0, max_level=30
    ),
    LearningMethod.TUTOR: MethodProfile(xp_per_hour=35, cost_per_hour=70, min_level=15),
    LearningMethod.BANDMATE: MethodProfile(
        xp_per_hour=25, cost_per_hour=0, session_cap=100
    ),
    LearningMethod.WORKSHOP: MethodProfile(
        xp_per_hour=50, cost_per_hour=150, min_level=25
    ),
    LearningMethod.PRACTICE: MethodProfile(xp_per_hour=10, cost_per_hour=0),
}


__all__ = ["LearningMethod", "MethodProfile", "METHOD_PROFILES"]
