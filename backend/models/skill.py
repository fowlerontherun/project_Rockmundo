from dataclasses import dataclass
from typing import Optional


@dataclass
class Skill:
    """Represents a learnable skill with progression."""

    id: int
    name: str
    category: str
    parent_id: Optional[int] = None
    xp: int = 0
    level: int = 1
    modifier: float = 1.0


__all__ = ["Skill"]
