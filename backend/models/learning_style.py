from __future__ import annotations

from enum import Enum
from typing import Dict

from backend.models.learning_method import LearningMethod


class LearningStyle(str, Enum):
    """Preferred way a user tends to learn new skills."""

    BALANCED = "balanced"
    VISUAL = "visual"
    AUDITORY = "auditory"
    READING = "reading"
    KINESTHETIC = "kinesthetic"


# XP multipliers per learning style and method
LEARNING_STYLE_BONUS: Dict[LearningStyle, Dict[LearningMethod, float]] = {
    LearningStyle.VISUAL: {LearningMethod.YOUTUBE: 1.2},
    LearningStyle.AUDITORY: {LearningMethod.TUTOR: 1.2},
    LearningStyle.READING: {LearningMethod.BOOK: 1.2},
    LearningStyle.KINESTHETIC: {
        LearningMethod.PRACTICE: 1.2,
        LearningMethod.APPRENTICESHIP: 1.1,
    },
}


__all__ = ["LearningStyle", "LEARNING_STYLE_BONUS"]
