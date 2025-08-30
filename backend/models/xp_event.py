from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional


@dataclass
class XPEvent:
    """Represents a temporary experience multiplier event."""

    id: Optional[int]
    name: str
    start_time: datetime
    end_time: datetime
    multiplier: float
    skill_target: Optional[str] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["start_time"] = self.start_time.isoformat()
        data["end_time"] = self.end_time.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "XPEvent":
        return cls(
            id=data.get("id"),
            name=data["name"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            multiplier=data["multiplier"],
            skill_target=data.get("skill_target"),
        )
