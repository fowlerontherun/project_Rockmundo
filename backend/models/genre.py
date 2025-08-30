
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Genre:
    """Represents a music genre with subgenres and demographic popularity."""

    id: int
    name: str
    subgenres: List[str] = field(default_factory=list)
    popularity: Dict[str, Dict[str, float]] = field(default_factory=dict)


__all__ = ["Genre"]

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("genres.id"), nullable=True)

    parent = relationship("Genre", remote_side=[id], backref="subgenres")
