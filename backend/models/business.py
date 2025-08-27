"""Dataclass representing player owned businesses."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Business:
    id: Optional[int]
    owner_id: int
    name: str
    business_type: str
    location: str
    startup_cost: int
    revenue_rate: int

    def to_dict(self) -> dict:
        """Return a serialisable representation."""
        return self.__dict__
