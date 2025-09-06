from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Perk:
    """Represents a gameplay perk unlocked via requirements."""

    id: int
    name: str
    description: str
    requirements: Dict[str, int] = field(default_factory=dict)


__all__ = ["Perk"]
