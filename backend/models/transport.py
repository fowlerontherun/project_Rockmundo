from sqlalchemy import Column, Integer, String, Float
from database import Base

class Transport(Base):
    __tablename__ = "transport"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    speed = Column(Float, nullable=False)
    fuel_cost_per_km = Column(Float, nullable=False)
    sleep_quality = Column(Float, nullable=False)
    maintenance_cost = Column(Float, nullable=False)
    travel_range_km = Column(Integer, nullable=False)
    type = Column(String, nullable=False)