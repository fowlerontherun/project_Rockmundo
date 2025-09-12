"""Models for property ownership and upgrades."""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


@dataclass
class PropertyType:
    """Represents a kind of property that can be purchased."""

    name: str
    base_price: int
    base_rent: int


@dataclass
class PropertyUpgradeSpec:
    """Schema describing an upgrade option for a property."""

    level: int
    cost: int
    rent_bonus: int
    rehearsal_bonus: int = 0


@dataclass
class PropertyData:
    """Convenience dataclass used by services."""

    id: Optional[int]
    owner_id: int
    name: str
    property_type: str
    location: str
    purchase_price: int
    base_rent: int
    level: int = 1

    def to_dict(self) -> dict:  # pragma: no cover - trivial
        return self.__dict__


class Property(Base):
    """SQLAlchemy model for a property owned by a band or user."""

    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    property_type = Column(String, nullable=False)
    location = Column(String, nullable=False)
    purchase_price = Column(Integer, nullable=False)
    base_rent = Column(Integer, nullable=False)
    level = Column(Integer, default=1)

    upgrades = relationship(
        "PropertyUpgrade", back_populates="property", cascade="all, delete-orphan"
    )


class PropertyUpgrade(Base):
    """SQLAlchemy model representing a property upgrade."""

    __tablename__ = "property_upgrades"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    level = Column(Integer, nullable=False)
    rent_bonus = Column(Integer, default=0)
    rehearsal_bonus = Column(Integer, default=0)

    property = relationship("Property", back_populates="upgrades")

