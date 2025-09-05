from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .item import Item


@dataclass
class Drug(Item):
    """Specialised :class:`Item` with drug-specific attributes."""

    effects: List[str] = field(default_factory=list)
    addiction_rate: float = 0.0
    duration: int = 0

    def __post_init__(self) -> None:  # pragma: no cover - trivial
        # Ensure drug attributes are mirrored in stats for persistence
        self.stats.setdefault("effects", self.effects)
        self.stats.setdefault("addiction_rate", self.addiction_rate)
        self.stats.setdefault("duration", self.duration)


__all__ = ["Drug"]
