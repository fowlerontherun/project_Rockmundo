from sqlalchemy import Column, Integer, String, Date
from database import Base

class SongAward(Base):
    __tablename__ = "song_awards"

    id = Column(Integer, primary_key=True)
    song_id = Column(Integer, nullable=False)
    award_name = Column(String, nullable=False)
    date_awarded = Column(Date, nullable=False)
    details = Column(String)