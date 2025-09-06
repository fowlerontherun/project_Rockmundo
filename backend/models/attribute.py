from dataclasses import dataclass


@dataclass
class Attribute:
    """Represents a trainable user attribute."""

    stat: str
    xp: int = 0
    level: int = 1


__all__ = ["Attribute"]
