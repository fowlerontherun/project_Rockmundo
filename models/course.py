from pydantic import BaseModel
from typing import Optional, Dict, Any


class Course(BaseModel):
    """Represents an academic course players can enroll in."""

    id: int
    skill_target: str
    duration: int
    prerequisites: Optional[Dict[str, Any]] = None
    prestige: bool = False


__all__ = ["Course"]
