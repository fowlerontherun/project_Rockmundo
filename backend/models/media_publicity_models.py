from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class MediaEvent(Base):
    __tablename__ = "media_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)  # e.g., interview, scandal, blog post, press release
    content = Column(Text)
    fame_impact = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
