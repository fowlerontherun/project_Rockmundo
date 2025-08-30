from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Campaign:
    """Represents a crowdfunding campaign."""

    id: int
    creator_id: int
    goal_cents: int
    pledged_cents: int = 0
    completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class Pledge:
    """Record of a pledge made toward a campaign."""

    id: int
    campaign_id: int
    backer_id: int
    amount_cents: int
    pledged_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class PayoutSchedule:
    """Defines how funds are shared once a campaign completes."""

    campaign_id: int
    creator_share: float = 0.8
    backer_share: float = 0.2
