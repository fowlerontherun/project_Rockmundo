from sqlalchemy import Column, Integer, Float, Boolean, String, Date, Time

from database import Base


class Gig(Base):
    """Database model representing a booked gig."""

    __tablename__ = "gigs"

    id = Column(Integer, primary_key=True)
    band_id = Column(Integer, nullable=False)
    venue_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    ticket_price = Column(Float, nullable=False)
    guarantee = Column(Float, default=0.0)
    ticket_split = Column(Float, default=0.0)
    support_band_id = Column(Integer, nullable=True)
    promoted = Column(Boolean, default=False)
    acoustic = Column(Boolean, default=False)
    audience_size = Column(Integer, default=0)
    total_earned = Column(Float, default=0.0)
    xp_gained = Column(Integer, default=0)
    fans_gained = Column(Integer, default=0)
    review = Column(String)
