from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Apprenticeship:
    """Link a student with a mentor for targeted skill training."""

    id: int | None
    student_id: int
    mentor_id: int
    mentor_type: str  # "npc" or "player"
    skill_id: int
    duration_days: int
    level_requirement: int
    start_date: str | None = None
    status: str = "pending"

    def __post_init__(self) -> None:
        if self.start_date is None and self.status == "active":
            self.start_date = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "mentor_id": self.mentor_id,
            "mentor_type": self.mentor_type,
            "skill_id": self.skill_id,
            "duration_days": self.duration_days,
            "level_requirement": self.level_requirement,
            "start_date": self.start_date,
            "status": self.status,
        }


__all__ = ["Apprenticeship"]
