from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class ReputationEvent:
    """Represents a single change to a user's reputation."""

    user_id: int
    change: int
    reason: str
    source: str
    timestamp: str | None = None

    def __post_init__(self) -> None:  # pragma: no cover - simple timestamp default
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class Reputation:
    """Simple in-memory representation of a user's reputation state."""

    user_id: int
    score: int = 0
    history: List[ReputationEvent] = field(default_factory=list)

    def add_event(self, event: ReputationEvent) -> None:
        self.score += event.change
        self.history.append(event)
