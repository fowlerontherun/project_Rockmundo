from dataclasses import dataclass
from typing import Optional


@dataclass
class Skill:
    """Represents a learnable skill."""

    id: int
    name: str
    category: str
    parent_id: Optional[int] = None


__all__ = ["Skill"]
