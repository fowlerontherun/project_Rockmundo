from sqlalchemy import Column, Integer, String, Date
from database import Base

class ChartEntry(Base):
    __tablename__ = "charts"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    chart_type = Column(String, nullable=False)  # daily, weekly, monthly, yearly
    category = Column(String, nullable=False)    # combined, digital, vinyl, streaming
    song_id = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)