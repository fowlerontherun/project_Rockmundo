from dataclasses import dataclass
from datetime import datetime


@dataclass
class LegacyMilestone:
    id: int | None
    band_id: int
    category: str
    description: str
    points: int
    achieved_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "band_id": self.band_id,
            "category": self.category,
            "description": self.description,
            "points": self.points,
            "achieved_at": self.achieved_at or datetime.utcnow().isoformat(),
        }
