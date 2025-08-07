from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database import Base

class Venue(Base):
    __tablename__ = "venues"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    city_id = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    fame_multiplier = Column(Float, nullable=False)