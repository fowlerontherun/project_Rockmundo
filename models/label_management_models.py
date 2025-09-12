# Label & Management models

"""Models for label, management and contract negotiations."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class Label:
    def __init__(self, name, genre_focus, max_roster, reputation, npc_owned=True):
        self.name = name
        self.genre_focus = genre_focus
        self.max_roster = max_roster
        self.reputation = reputation
        self.npc_owned = npc_owned

class ManagementContract:
    def __init__(self, manager_id, band_id, cut_percentage, perks, active=True):
        self.manager_id = manager_id
        self.band_id = band_id
        self.cut_percentage = cut_percentage
        self.perks = perks
        self.active = active

class LabelContract:
    def __init__(self, label_id, band_id, revenue_split, advance_payment, min_releases, active=True):
        self.label_id = label_id
        self.band_id = band_id
        self.revenue_split = revenue_split
        self.advance_payment = advance_payment
        self.min_releases = min_releases
        self.active = active


class NegotiationStage(str, Enum):
    """Simple state machine for contract negotiations."""

    OFFER = "offer"
    COUNTER = "counter"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass
class ClauseTemplate:
    """Represents a negotiable contract clause with a default value."""

    key: str
    description: str
    default: Any


DEFAULT_CLAUSES = [
    ClauseTemplate("advance_cents", "Upfront payment to the band", 0),
    ClauseTemplate("royalty_rate", "Revenue percentage for the band", 0.0),
    ClauseTemplate("marketing_budget_cents", "Label-funded marketing spend", 0),
    ClauseTemplate("distribution_fee_rate", "Percentage fee for distribution services", 0.0),
    ClauseTemplate("rights_reversion_months", "Months until rights revert to the band", 0),
    ClauseTemplate("release_commitment", "Minimum releases label commits to", 0),
]


@dataclass
class ContractNegotiation:
    """In-memory record of an ongoing negotiation."""

    id: int
    label_id: int
    band_id: int
    terms: Dict[str, Any]
    stage: NegotiationStage = NegotiationStage.OFFER
