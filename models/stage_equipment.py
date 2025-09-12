from dataclasses import dataclass, field
from typing import Dict


@dataclass
class StageEquipment:
    """Represents a piece of stage equipment with genre affinities."""

    id: int
    name: str
    category: str
    brand: str
    rating: int  # 1-11 stars
    genre_affinity: Dict[str, float] = field(default_factory=dict)


__all__ = ["StageEquipment"]
