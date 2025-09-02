"""Data model for online tutorials used in learning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class OnlineTutorial:
    """Representation of an online tutorial video.

    Attributes:
        video_url: Link or identifier for the tutorial video.
        skill: Skill the tutorial teaches.
        xp_rate: XP gained per completion.
        plateau_level: Level after which the tutorial is less effective.
        rarity_weight: Weight used when selecting tutorials based on rarity.
    """

    id: Optional[int]
    video_url: str
    skill: str
    xp_rate: int
    plateau_level: int
    rarity_weight: int


__all__ = ["OnlineTutorial"]
