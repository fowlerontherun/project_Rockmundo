from typing import Dict, List, Optional

from pydantic import BaseModel


class SkillSchema(BaseModel):
    id: Optional[int] = None
    name: str
    category: str
    parent_id: Optional[int] = None
    prerequisites: Dict[int, int] = {}


class SkillPrerequisitesSchema(BaseModel):
    prerequisites: Dict[int, int]

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

__all__ = [
    "SkillSchema",
    "SkillPrerequisitesSchema",
    "GenreSchema",
    "StageEquipmentSchema",
]

__all__ = ["SkillSchema", "GenreSchema", "StageEquipmentSchema"]
