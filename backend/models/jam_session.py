from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Set


@dataclass
class AudioStream:
    """Represents a participant's outbound audio stream."""

    user_id: int
    stream_id: str
    codec: str
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    premium: bool = False


@dataclass
class Participant:
    user_id: int
    joined_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class JamSession:
    """In-memory representation of a jam session."""

    id: str
    host_id: int
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    participants: Dict[int, Participant] = field(default_factory=dict)
    streams: Dict[int, AudioStream] = field(default_factory=dict)
    invites: Set[int] = field(default_factory=set)

    def add_participant(self, user_id: int) -> None:
        self.participants[user_id] = Participant(user_id=user_id)

    def remove_participant(self, user_id: int) -> None:
        self.participants.pop(user_id, None)
        self.streams.pop(user_id, None)
