from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Track:
    """Basic music track used during production."""

    id: int
    title: str
    band_id: int
    duration_sec: int
    sessions: List[int] = field(default_factory=list)
    mixing_id: Optional[int] = None
    release: Optional["ReleaseMetadata"] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "band_id": self.band_id,
            "duration_sec": self.duration_sec,
            "sessions": list(self.sessions),
            "mixing_id": self.mixing_id,
            "release": self.release.to_dict() if self.release else None,
        }


@dataclass
class StudioSession:
    """Represents a recording session for a track."""

    id: int
    track_id: int
    scheduled_date: str
    engineer: str
    cost_cents: int

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class MixingSession:
    """Represents a mixing/mastering session."""

    id: int
    track_id: int
    engineer: str
    cost_cents: int
    mastered: bool = False

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class ReleaseMetadata:
    """Metadata about a released track."""

    track_id: int
    release_date: str
    channels: List[str]
    sales: int = 0
    chart_position: Optional[int] = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()
