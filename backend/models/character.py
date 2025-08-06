from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    genre = Column(String)
    trait = Column(String)
    birthplace = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
