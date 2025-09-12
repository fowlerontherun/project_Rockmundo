from dataclasses import dataclass
from datetime import datetime


@dataclass
class SongPopularity:
    """Represents the popularity score of a song at a point in time."""

    song_id: int
    popularity_score: float
    updated_at: datetime
