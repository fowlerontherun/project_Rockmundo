from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Release(Base):
    __tablename__ = "releases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    format = Column(Enum("single", "ep", "lp", name="release_format"))
    release_date = Column(DateTime(timezone=True), server_default=func.now())
    total_runtime = Column(Integer, default=0)
    band_id = Column(Integer, ForeignKey("bands.id"), nullable=True)
    collaboration_id = Column(Integer, ForeignKey("band_collaborations.id"), nullable=True)
    distribution_channels = Column(Text)

    tracks = relationship("Track", order_by="Track.track_number", cascade="all, delete-orphan")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    release_id = Column(Integer, ForeignKey("releases.id"))
    title = Column(String, index=True)
    duration = Column(Integer)  # in seconds
    track_number = Column(Integer)
