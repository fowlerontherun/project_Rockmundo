from dataclasses import dataclass, field
from enum import Enum
from typing import List


class EventType(str, Enum):
    """Enumeration of supported in-game event types."""

    WORKSHOP = "WORKSHOP"


@dataclass
class Event:
    """Generic event record used for workshops and similar activities."""

    id: int
    type: EventType
    name: str
    skill_target: str
    ticket_cost: int
    xp_reward: int
    capacity: int
    attendees: List[int] = field(default_factory=list)

    def has_space(self) -> bool:
        """Return True if more attendees can register."""

        return len(self.attendees) < self.capacity
