from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class NegotiationStage(str, Enum):
    """Possible states of a sponsorship negotiation."""

    OFFER = "offer"
    COUNTER = "counter"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass
class SponsorshipNegotiation:
    """In-memory representation of a sponsorship negotiation."""

    id: int
    venue_id: int
    sponsor_name: str
    terms: Dict[str, Any]
    stage: NegotiationStage = NegotiationStage.OFFER
