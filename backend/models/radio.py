from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class RadioStation:
    """Simple representation of a radio station."""

    id: int
    name: str
    owner_id: int


@dataclass
class RadioEpisode:
    """Episode or show belonging to a radio station."""

    id: int
    station_id: int
    title: str
    recorded_at: datetime | None = None


@dataclass
class RadioSchedule:
    """Scheduled slot for broadcasting an episode."""

    id: int
    station_id: int
    episode_id: int
    start_time: datetime
    end_time: datetime | None = None
    status: str = "scheduled"
