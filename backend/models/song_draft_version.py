from __future__ import annotations

"""Version snapshot for song drafts."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class SongDraftVersion:
    """Represents a saved version of a song draft."""

    author_id: int
    lyrics: str
    chords: Optional[str] = None
    themes: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
