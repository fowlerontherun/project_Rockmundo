from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Achievement:
    """Definition of an achievement or badge."""
    id: int
    code: str
    name: str
    description: str


@dataclass
class PlayerAchievement:
    """Track a player's progress toward an achievement."""
    user_id: int
    achievement_id: int
    progress: int = 0
    unlocked_at: Optional[datetime] = None
