from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Tutor:
    """Represents a skill tutor available for hire."""

    id: int | None
    name: str
    specialization: str
    hourly_rate: int


__all__ = ["Tutor"]
