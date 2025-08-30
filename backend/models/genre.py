from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Genre:
    """Represents a music genre with subgenres and demographic popularity."""

    id: int
    name: str
    subgenres: List[str] = field(default_factory=list)
    popularity: Dict[str, Dict[str, float]] = field(default_factory=dict)


__all__ = ["Genre"]
