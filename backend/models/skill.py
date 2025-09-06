from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class SkillSpecialization:
    """Metadata describing a specialization for a skill."""

    name: str
    related_skills: Dict[int, int]
    bonus: float = 0.1


@dataclass
class Skill:
    """Represents a learnable skill with progression."""

    id: int
    name: str
    category: str
    parent_id: Optional[int] = None
    xp: int = 0
    level: int = 1
    modifier: float = 1.0
    # Mapping of skill_id -> required level
    prerequisites: Dict[int, int] = field(default_factory=dict)
    specializations: Dict[str, SkillSpecialization] = field(default_factory=dict)
    specialization: Optional[str] = None


__all__ = ["Skill", "SkillSpecialization"]
