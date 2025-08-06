from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class SongDistribution(Base):
    __tablename__ = "song_distributions"

    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, ForeignKey("songs.id"), unique=True)

    # Sales + streams
    digital_sales = Column(Integer, default=0)
    vinyl_sales = Column(Integer, default=0)
    streams = Column(Integer, default=0)

    # Production costs
    digital_cost = Column(Float, default=0.0)
    vinyl_cost = Column(Float, default=0.0)

    # Revenue (before/after costs)
    digital_revenue = Column(Float, default=0.0)
    vinyl_revenue = Column(Float, default=0.0)
    streaming_revenue = Column(Float, default=0.0)
