from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class Addiction(BaseModel):
    """Represents a user's addiction to a particular substance."""

    user_id: int
    substance: str
    level: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def touch(self) -> None:
        now = datetime.utcnow()
        if self.created_at is None:
            self.created_at = now
        self.updated_at = now


__all__ = ["Addiction"]
