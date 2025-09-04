from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PlayerChemistry(Base):
    """Tracks chemistry between two players."""

    __tablename__ = "player_chemistry"

    id = Column(Integer, primary_key=True, index=True)
    player_a_id = Column(Integer, index=True, nullable=False)
    player_b_id = Column(Integer, index=True, nullable=False)
    score = Column(Integer, default=50)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
