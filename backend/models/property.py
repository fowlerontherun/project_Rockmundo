from dataclasses import dataclass
from typing import Optional


@dataclass
class PropertyType:
    """Represents a kind of property that can be purchased."""
    name: str
    base_price: int
    base_rent: int


@dataclass
class PropertyUpgrade:
    """Describes an upgrade applied to a property."""
    level: int
    cost: int
    rent_bonus: int
    rehearsal_bonus: int = 0


@dataclass
class Property:
    """A property owned by a band or user."""
    id: Optional[int]
    owner_id: int
    name: str
    property_type: str
    location: str
    purchase_price: int
    base_rent: int
    level: int = 1

    def to_dict(self) -> dict:
        return self.__dict__
