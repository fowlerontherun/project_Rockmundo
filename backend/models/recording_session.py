from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List


@dataclass
class RecordingSession:
    """Represents a scheduled studio recording session."""

    id: int
    band_id: int
    studio: str
    start: str
    end: str
    track_statuses: Dict[int, str] = field(default_factory=dict)
    personnel: List[int] = field(default_factory=list)
    cost_cents: int = 0
    environment_quality: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "band_id": self.band_id,
            "studio": self.studio,
            "start": self.start,
            "end": self.end,
            "track_statuses": dict(self.track_statuses),
            "personnel": list(self.personnel),
            "cost_cents": self.cost_cents,
            "environment_quality": self.environment_quality,
            "created_at": self.created_at,
        }


__all__ = ["RecordingSession"]
