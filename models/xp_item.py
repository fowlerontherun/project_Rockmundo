from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class XPItem:
    """Represents an XP modifying item that can be used by players."""

    id: Optional[int]
    name: str
    effect_type: Literal["flat", "boost"]
    amount: float
    duration: int
