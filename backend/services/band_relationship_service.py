from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from backend.models.band_relationship import BandRelationship


@dataclass
class _InMemoryDB:
    """Very small in-memory storage used when no database is supplied."""

    items: Dict[int, BandRelationship]
    counter: int = 1

    def insert_band_relationship(self, rel: BandRelationship) -> None:
        rel.id = self.counter
        self.items[self.counter] = rel
        self.counter += 1

    def get_band_relationships(
        self, band_id: int, relationship_type: Optional[str] = None
    ) -> List[dict]:
        result = []
        for rel in self.items.values():
            if not rel.active:
                continue
            if band_id not in (rel.band_a_id, rel.band_b_id):
                continue
            if relationship_type and rel.type != relationship_type:
                continue
            result.append(rel.to_dict())
        return result

    def get_relationship(self, band_a_id: int, band_b_id: int) -> Optional[BandRelationship]:
        for rel in self.items.values():
            if not rel.active:
                continue
            if {rel.band_a_id, rel.band_b_id} == {band_a_id, band_b_id}:
                return rel
        return None

    def deactivate_relationship(self, band_a_id: int, band_b_id: int) -> None:
        rel = self.get_relationship(band_a_id, band_b_id)
        if rel:
            rel.active = False


class BandRelationshipService:
    """Service layer providing helpers for band relationships."""

    def __init__(self, db: Optional[object] = None):
        # Allow injection of a real DB but fall back to in-memory storage for
        # tests or simple usage.
        self.db = db or _InMemoryDB({})

    # ------------------------------------------------------------------
    def create_relationship(
        self,
        band_a_id: int,
        band_b_id: int,
        relationship_type: str,
        affinity: Optional[int] = None,
        compatibility: Optional[int] = None,
        high_profile: bool = False,
        networking: int = 0,
    ) -> dict:
        if high_profile and networking < 60:
            raise ValueError("Networking too low for high-profile collaboration")
        rel = BandRelationship(
            id=None,
            band_a_id=band_a_id,
            band_b_id=band_b_id,
            type=relationship_type,
            affinity=affinity,
            compatibility=compatibility,
        )
        self.db.insert_band_relationship(rel)
        return rel.to_dict()

    # ------------------------------------------------------------------
    def get_relationships(
        self, band_id: int, relationship_type: Optional[str] = None
    ) -> List[dict]:
        return self.db.get_band_relationships(band_id, relationship_type)

    # ------------------------------------------------------------------
    def get_relationship(self, band_a_id: int, band_b_id: int) -> Optional[dict]:
        rel = self.db.get_relationship(band_a_id, band_b_id)
        return rel.to_dict() if rel else None

    # ------------------------------------------------------------------
    def end_relationship(self, band_a_id: int, band_b_id: int) -> dict:
        self.db.deactivate_relationship(band_a_id, band_b_id)
        return {"status": "relationship ended"}

    # ------------------------------------------------------------------
    def get_relationship_modifier(self, band_a_id: int, band_b_id: int) -> float:
        """Return a multiplier based on affinity & compatibility.

        The modifier ranges roughly between 0.5 and 1.5. Values above 1 boost
        outcomes while values below 1 penalise them.
        """

        rel = self.db.get_relationship(band_a_id, band_b_id)
        if not rel:
            return 1.0
        score = (rel.affinity + rel.compatibility) / 2  # 0-100
        return 1 + (score - 50) / 100
