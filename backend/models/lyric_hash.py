from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LyricHash:
    """Persisted hash of song lyrics for originality checks."""

    id: int
    song_id: int
    hash: str
    created_at: datetime = field(default_factory=datetime.utcnow)
