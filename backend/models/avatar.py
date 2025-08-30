from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# SQLAlchemy base for the avatar models
Base = declarative_base()

# Import the Character model for relationship support. The Character model
# lives in its own module with a separate ``Base`` registry.  We only need the
# class here so that SQLAlchemy can map the relationship; the metadata is
# created separately in tests or application startup.
try:  # pragma: no cover - optional import for test environments
    from models.character import Character  # type: ignore
except Exception:  # pragma: no cover
    Character = None  # type: ignore


class Avatar(Base):
    """Represents a player's visual avatar.

    The model stores identity information, appearance customisation and basic
    statistics.  Each avatar is linked to a :class:`Character` via a foreign key
    to demonstrate relationships between tables.
    """

    __tablename__ = "avatars"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False, unique=True)
    nickname = Column(String, nullable=False)

    # --- Appearance -------------------------------------------------------
    body_type = Column(String, nullable=False)
    skin_tone = Column(String, nullable=False)
    face_shape = Column(String, nullable=False)
    hair_style = Column(String, nullable=False)
    hair_color = Column(String, nullable=False)
    top_clothing = Column(String, nullable=False)
    bottom_clothing = Column(String, nullable=False)
    shoes = Column(String, nullable=False)
    accessory = Column(String)
    held_item = Column(String)
    pose = Column(String)

    # --- Stats ------------------------------------------------------------
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    health = Column(Integer, default=100)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to Character for convenience. ``viewonly`` avoids SQLAlchemy
    # trying to manage the other side which may be defined elsewhere with a
    # different registry.
    character = relationship(Character, lazy="joined", viewonly=True)

