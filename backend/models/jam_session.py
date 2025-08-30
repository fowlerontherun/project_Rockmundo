from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AudioStream:
    """Represents a participant's outbound audio stream."""

    user_id: int
    stream_id: str
    codec: str
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    premium: bool = False


@dataclass
class JamSession:
    """Lightweight representation of a jam session."""

    id: str
    host_id: int
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
