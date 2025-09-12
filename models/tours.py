from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Tour(Base):
    __tablename__ = "tours"
    id = Column(Integer, primary_key=True)
    band_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    start_date = Column(Date)

class TourStop(Base):
    __tablename__ = "tour_stops"
    id = Column(Integer, primary_key=True)
    tour_id = Column(Integer, ForeignKey("tours.id"))
    city_id = Column(Integer)
    venue_id = Column(Integer)
    date = Column(Date)