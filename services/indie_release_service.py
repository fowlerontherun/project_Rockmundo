from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from models.label_management_models import ClauseTemplate
from backend.services.economy_service import EconomyService


@dataclass
class IndieRelease:
    """Record of a purchased indie release package."""

    id: int
    band_id: int
    distribution: str
    promotion: str
    physical: str
    cost_cents: int
    vendor_terms: Dict[str, Any] = field(default_factory=dict)


class IndieReleaseService:
    """Service to purchase indie release packages and track assets."""

    def __init__(self, economy: Optional[EconomyService] = None):
        self.economy = economy or EconomyService()
        self.releases: Dict[int, IndieRelease] = {}
        self._next_id = 1

        # Pricing tables in cents
        self.distribution_packages = {
            "digital": 5000,
            "worldwide": 15000,
        }
        self.promotion_packages = {
            "none": 0,
            "standard": 8000,
            "plus": 20000,
        }
        self.physical_packages = {
            "none": 0,
            "cd": 7000,
            "vinyl": 12000,
        }

        # Clause templates reused for optional third-party vendors
        self.vendor_clauses = [
            ClauseTemplate("vendor_name", "Third-party vendor", ""),
            ClauseTemplate("vendor_fee_cents", "Vendor fee in cents", 0),
        ]

    # ------------------------------------------------------------------
    def purchase_release(
        self,
        band_id: int,
        distribution: str,
        promotion: str,
        physical: str,
        vendor_terms: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Purchase a release package and deduct the cost from the band."""

        cost = (
            self.distribution_packages.get(distribution, 0)
            + self.promotion_packages.get(promotion, 0)
            + self.physical_packages.get(physical, 0)
        )

        # Deduct funds
        self.economy.withdraw(band_id, cost)

        # Merge vendor terms with clause defaults
        vendor_terms = vendor_terms or {}
        final_vendor_terms = {
            c.key: vendor_terms.get(c.key, c.default) for c in self.vendor_clauses
        }

        release = IndieRelease(
            id=self._next_id,
            band_id=band_id,
            distribution=distribution,
            promotion=promotion,
            physical=physical,
            cost_cents=cost,
            vendor_terms=final_vendor_terms,
        )
        self.releases[self._next_id] = release
        self._next_id += 1
        return release.__dict__

    def list_releases(self, band_id: int) -> List[Dict[str, Any]]:
        """List all purchased releases for a band."""

        return [r.__dict__ for r in self.releases.values() if r.band_id == band_id]
