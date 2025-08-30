from datetime import datetime
from dataclasses import dataclass


@dataclass
class EventEffect:
    """Represents a temporary effect applied to a user."""

    user_id: int
    skill: str | None
    effect: str
    start: str
    duration: int

    def __init__(self, user_id: int, effect: str, duration: int, skill: str | None = None, start: str | None = None):
        self.user_id = user_id
        self.skill = skill
        self.effect = effect
        self.start = start or datetime.utcnow().isoformat()
        self.duration = duration

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "skill": self.skill,
            "effect": self.effect,
            "start": self.start,
            "duration": self.duration,
        }
