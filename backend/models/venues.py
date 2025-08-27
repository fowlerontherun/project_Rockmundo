"""Database model and dataclass for venues.

Historically the project only stored minimal information about a venue –
essentially a name, a city identifier and a fame multiplier used by the tour
system.  The admin management features introduced in this task require more
details and the ability to link venues to an owner.  To remain compatible with
existing SQLAlchemy usage while also providing a light‑weight data container for
the new services, this module now exposes both a SQLAlchemy model and a simple
dataclass representation.

Only the columns used elsewhere in the code base are preserved and new optional
fields are added so that older migrations continue to work.
"""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import Column, Float, Integer, String

from database import Base


class Venue(Base):
    """SQLAlchemy model used by parts of the application."""

    __tablename__ = "venues"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    city_id = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    fame_multiplier = Column(Float, nullable=False)

    # --- new fields ---
    owner_id = Column(Integer, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    rental_cost = Column(Integer, nullable=True)


@dataclass
class VenueModel:
    """Dataclass used by the administrative CRUD service."""

    id: Optional[int]
    owner_id: int
    name: str
    city: str
    country: str
    capacity: int
    rental_cost: int

    def to_dict(self) -> dict:
        """Return a serialisable representation."""
        return self.__dict__
