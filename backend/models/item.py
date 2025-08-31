from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ItemCategory:
    """Simple item category descriptor."""

    name: str
    description: str = ""


@dataclass
class Item:
    """Generic inventory item with arbitrary stats."""

    id: Optional[int]
    name: str
    category: str
    stats: Dict[str, float] = field(default_factory=dict)


__all__ = ["ItemCategory", "Item"]
