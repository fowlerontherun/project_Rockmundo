from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

# additional imports for extended band modelling
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

Base = declarative_base()

class Band(Base):
    __tablename__ = "bands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    founder_id = Column(Integer, ForeignKey("characters.id"))
    genre_id = Column(Integer, ForeignKey("genres.id"))
    formed_at = Column(DateTime(timezone=True), server_default=func.now())
    # aggregate skill metric and upcoming performance quality modifier
    skill = Column(Integer, default=0)
    performance_quality = Column(Integer, default=0)

class BandMember(Base):
    __tablename__ = "band_members"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    band_id = Column(Integer, ForeignKey("bands.id"))
    role = Column(String)  # e.g., "lead guitar", "vocals"
    is_manager = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

class BandCollaboration(Base):
    __tablename__ = "band_collaborations"

    id = Column(Integer, primary_key=True, index=True)
    band_1_id = Column(Integer, ForeignKey("bands.id"))
    band_2_id = Column(Integer, ForeignKey("bands.id"))
    project_type = Column(String)  # "song" or "album"
    title = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# Extended models for band lineup, skills and availability
# ---------------------------------------------------------------------------


class BandLineupSlot(Base):
    """Represents a required role in the band's lineup."""

    __tablename__ = "band_lineup_slots"

    id = Column(Integer, primary_key=True, index=True)
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=False)
    role = Column(String, nullable=False)
    required_skill = Column(String, nullable=True)
    min_level = Column(Integer, default=0)


class BandSkill(Base):
    """Tracks a band's proficiency for a given skill."""

    __tablename__ = "band_skills"

    id = Column(Integer, primary_key=True, index=True)
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=False)
    skill_id = Column(Integer, nullable=False)
    level = Column(Integer, default=0)


class BandAvailability(Base):
    """Availability window for rehearsal or events."""

    __tablename__ = "band_availability"

    id = Column(Integer, primary_key=True, index=True)
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=False)
    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True), nullable=False)


# Convenience dataclasses for service layer consumption


@dataclass
class AvailabilityWindow:
    band_id: int
    start: datetime
    end: datetime


@dataclass
class LineupSlot:
    band_id: int
    role: str
    required_skill: Optional[str] = None
    min_level: int = 0


@dataclass
class SkillProgress:
    band_id: int
    skill: str
    level: int
