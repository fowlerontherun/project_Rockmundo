from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TicketTier:
    """Simple ticket tier representation for a festival."""

    name: str
    price_cents: int
    capacity: int
    sold: int = 0


@dataclass
class Slot:
    """Represents a stage timeslot that can host a band."""

    stage: str
    index: int
    band_id: Optional[int] = None


@dataclass
class Stage:
    """Collection of slots for a stage."""

    name: str
    slots: List[Slot] = field(default_factory=list)


@dataclass
class Sponsor:
    """Festival sponsor contributing funds."""

    name: str
    contribution_cents: int


@dataclass
class FestivalBuilder:
    """Aggregate object capturing a festival under construction."""

    id: int
    name: str
    owner_id: int
    stages: Dict[str, Stage] = field(default_factory=dict)
    ticket_tiers: List[TicketTier] = field(default_factory=list)
    sponsors: List[Sponsor] = field(default_factory=list)
    finances: Dict[str, int] = field(default_factory=lambda: {"revenue": 0, "payouts": 0})
    tickets: List[object] = field(default_factory=list)  # ticketing_models.Ticket instances
