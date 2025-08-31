from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ArrangementTrack:
    id: int
    song_id: int
    track_type: str
    performer: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "song_id": self.song_id,
            "track_type": self.track_type,
            "performer": self.performer,
            "notes": self.notes,
        }


__all__ = ["ArrangementTrack"]
