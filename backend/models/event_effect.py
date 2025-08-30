from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class EventEffect:
    """Represents a temporary effect applied to a user."""

    user_id: int
    skill_id: Optional[int]
    effect: str
    start: str
    duration: int

    def __init__(
        self,
        user_id: int,
        effect: str,
        duration: int,
        skill_id: Optional[int] = None,
        start: Optional[str] = None,
    ):
        self.user_id = user_id
        self.skill_id = skill_id
        self.effect = effect
        self.start = start or datetime.utcnow().isoformat()
        self.duration = duration

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "skill_id": self.skill_id,
            "effect": self.effect,
            "start": self.start,
            "duration": self.duration,
        }
