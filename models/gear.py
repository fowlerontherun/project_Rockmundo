from dataclasses import dataclass, field
from typing import List


@dataclass
class StatModifier:
    """Simple stat modifier applied by gear."""

    stat: str
    amount: float


@dataclass
class BaseItem:
    """Base blueprint for craftable gear."""

    name: str
    durability: int
    base_modifiers: List[StatModifier] = field(default_factory=list)


@dataclass
class GearComponent:
    """Component that influences crafting success and stats."""

    name: str
    success_rate: float = 1.0
    durability_bonus: int = 0
    modifiers: List[StatModifier] = field(default_factory=list)


@dataclass
class GearItem:
    """Crafted gear with durability and stat modifiers."""

    id: int
    name: str
    durability: int
    modifiers: List[StatModifier] = field(default_factory=list)


__all__ = ["StatModifier", "BaseItem", "GearComponent", "GearItem"]
