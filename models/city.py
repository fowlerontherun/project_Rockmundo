"""Dataclass representing a game city with economic trends."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class City:
    """Represents a city's economic and cultural data."""

    name: str
    population: int
    style_preferences: Dict[str, float]
    market_index: float = 1.0
    event_modifier: float = 1.0

    def popular_style(self) -> str:
        """Return the style with highest preference."""
        if not self.style_preferences:
            return "unknown"
        return max(self.style_preferences, key=self.style_preferences.get)


__all__ = ["City"]
