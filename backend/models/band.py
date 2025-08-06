from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Band(Base):
    __tablename__ = "bands"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    founder_id = Column(Integer, ForeignKey("characters.id"))
    genre = Column(String)
    formed_at = Column(DateTime(timezone=True), server_default=func.now())

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
