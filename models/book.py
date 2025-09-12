"""Simple model for skill books used in training."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Book:
    """Representation of a skill book.

    Attributes:
        title: Title of the book.
        genre: Thematic genre the book belongs to.
        rarity: Availability descriptor.
        max_skill_level: Highest skill level the book can teach.
    """

    id: Optional[int]
    title: str
    genre: str
    rarity: str
    max_skill_level: int
    price_cents: int = 0
    stock: int = 0


__all__ = ["Book"]

