from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class RoyaltyTier:
    """Represents a thresholded royalty rate."""

    threshold_units: int
    rate: float


@dataclass
class RecordContract:
    """Typed representation of a recording contract."""

    advance_cents: int
    royalty_tiers: List[RoyaltyTier] = field(default_factory=list)
    term_months: int = 0
    territory: str = "worldwide"
    recoupable_budgets_cents: int = 0
    options: List[str] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)
    marketing_budget_cents: int = 0
    distribution_fee_rate: float = 0.0
    rights_reversion_months: int = 0
    release_commitment: int = 0
