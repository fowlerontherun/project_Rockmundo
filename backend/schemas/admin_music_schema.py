from typing import Dict, List, Optional

from pydantic import BaseModel


class SkillSchema(BaseModel):
    id: int
    name: str
    category: str
    parent_id: Optional[int] = None


class GenreSchema(BaseModel):
    id: int
    name: str
    subgenres: List[str] = []
    popularity: Dict[str, Dict[str, float]] = {}

class StageEquipmentSchema(BaseModel):
    id: int
    name: str
    category: str
    brand: str
    rating: int
    genre_affinity: Dict[str, float] = {}


__all__ = ["SkillSchema", "GenreSchema", "StageEquipmentSchema"]