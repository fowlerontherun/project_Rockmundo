from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

try:  # pragma: no cover - optional import for test environments
    from models.character import Base as CharacterBase, Character  # type: ignore  # noqa: I001
    Base = CharacterBase
except Exception:  # pragma: no cover
    Base = declarative_base()
    Character = None  # type: ignore


class Avatar(Base):
    """Represents a player's visual avatar.

    The model stores identity information, appearance customisation and basic
    statistics.  Each avatar is linked to a :class:`Character` via a foreign key
    to demonstrate relationships between tables.
    """

    __tablename__ = "avatars"

    id = Column(Integer, primary_key=True, index=True)
    # ``use_alter`` allows this foreign key to be created even when the
    # referenced table lives in a separate metadata registry.  SQLAlchemy will
    # emit an ``ALTER TABLE`` after creation which avoids dependency issues in
    # testing environments where ``characters`` may be created separately.
    character_id = Column(
        Integer,
        ForeignKey("characters.id", use_alter=True, link_to_name=True),
        nullable=False,
        unique=True,
    )
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
    # Mood is stored as a simple 0-100 scale where 50 is neutral.  This allows
    # lightweight persistence of how an avatar is feeling which can then be
    # influenced by lifestyle scores and random events.
    mood = Column(Integer, default=50)
    stamina = Column(Integer, default=50)
    fatigue = Column(Integer, default=0)
    charisma = Column(Integer, default=50)
    intelligence = Column(Integer, default=50)
    creativity = Column(Integer, default=50)
    discipline = Column(Integer, default=50)
    resilience = Column(Integer, default=50)
    luck = Column(Integer, default=0)
    social_media = Column(Integer, default=0)
    tech_savvy = Column(Integer, default=0)
    networking = Column(Integer, default=0)
    leadership = Column(Integer, default=0)
    stage_presence = Column(Integer, default=50)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to Character for convenience. ``viewonly`` avoids SQLAlchemy
    # trying to manage the other side which may be defined elsewhere with a
    # different registry.
    character = relationship(Character, lazy="joined", viewonly=True)

