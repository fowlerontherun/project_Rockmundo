from sqlalchemy import Column, Integer, String, Float, Date
from database import Base

class SalesData(Base):
    __tablename__ = "sales_data"

    id = Column(Integer, primary_key=True)
    song_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    format = Column(String, nullable=False)  # 'digital', 'vinyl'
    units_sold = Column(Integer, nullable=False)
    revenue = Column(Float, nullable=False)
    production_cost = Column(Float, nullable=False)