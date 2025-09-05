from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class CollaborationStatus(str, Enum):
    """Possible states for a collaboration request."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Influencer(BaseModel):
    """Simplified representation of a social media influencer."""

    id: int
    name: str
    niche: Optional[str] = None
    followers: int = 0


class Collaboration(BaseModel):
    """Collaboration between two influencers."""

    id: int
    initiator_id: int
    partner_id: int
    details: Optional[str] = None
    status: CollaborationStatus = CollaborationStatus.PENDING
    created_at: datetime = datetime.utcnow()

