from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Enum
from database import Base
from datetime import datetime

class DigitalSale(Base):
    __tablename__ = "digital_sales"
    id = Column(Integer, primary_key=True)
    song_id = Column(Integer, nullable=False)
    buyer_id = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class VinylSale(Base):
    __tablename__ = "vinyl_sales"
    id = Column(Integer, primary_key=True)
    album_id = Column(Integer, nullable=False)
    buyer_id = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    production_cost = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Stream(Base):
    __tablename__ = "streams"
    id = Column(Integer, primary_key=True)
    song_id = Column(Integer, nullable=False)
    listener_id = Column(Integer, nullable=False)
    region = Column(String)
    platform = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)