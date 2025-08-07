from sqlalchemy import Column, Integer, Float, Boolean, String, Date, ForeignKey
from database import Base

class Gig(Base):
    __tablename__ = "gigs"

    id = Column(Integer, primary_key=True)
    band_id = Column(Integer, nullable=False)
    venue_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    ticket_price = Column(Float, nullable=False)
    support_band_id = Column(Integer, nullable=True)
    promoted = Column(Boolean, default=False)
    acoustic = Column(Boolean, default=False)
    audience_size = Column(Integer, default=0)
    total_earned = Column(Float, default=0.0)
    review = Column(String)