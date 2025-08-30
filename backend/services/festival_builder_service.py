from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from backend.models.festival_builder import (
    FestivalBuilder,
    Slot,
    Stage,
    Sponsor,
    TicketTier,
)
from backend.models.ticketing_models import Ticket
from services.economy_service import EconomyService
from services.legacy_service import LegacyService

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class FestivalError(Exception):
    pass


class BookingConflictError(FestivalError):
    """Raised when attempting to double book a slot."""


class FestivalBuilderService:
    """Service handling festival creation and basic finance tracking."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        economy: EconomyService | None = None,
        legacy: LegacyService | None = None,
    ):
        self.db_path = str(db_path or DB_PATH)
        self.economy = economy or EconomyService(db_path=self.db_path)
        self.legacy = legacy or LegacyService(db_path=self.db_path)
        self.economy.ensure_schema()
        self.legacy.ensure_schema()
        self._festivals: Dict[int, FestivalBuilder] = {}
        self._id_seq = 1

    # ---------------- Festival lifecycle ----------------
    def create_festival(
        self,
        name: str,
        owner_id: int,
        stages: Dict[str, int],
        ticket_tiers: List[Dict[str, int]],
        sponsors: Optional[List[Dict[str, int]]] = None,
    ) -> int:
        stage_objs: Dict[str, Stage] = {}
        for stage_name, slot_count in stages.items():
            slots = [Slot(stage=stage_name, index=i) for i in range(int(slot_count))]
            stage_objs[stage_name] = Stage(name=stage_name, slots=slots)

        tier_objs = [
            TicketTier(
                name=t["name"],
                price_cents=int(t["price_cents"]),
                capacity=int(t["capacity"]),
            )
            for t in ticket_tiers
        ]

        sponsor_objs: List[Sponsor] = []
        for s in sponsors or []:
            sponsor_objs.append(
                Sponsor(name=s["name"], contribution_cents=int(s["contribution_cents"]))
            )

        fest = FestivalBuilder(
            id=self._id_seq,
            name=name,
            owner_id=owner_id,
            stages=stage_objs,
            ticket_tiers=tier_objs,
            sponsors=sponsor_objs,
        )
        self._festivals[fest.id] = fest
        self._id_seq += 1
        return fest.id

    def get_festival(self, festival_id: int) -> FestivalBuilder:
        fest = self._festivals.get(int(festival_id))
        if not fest:
            raise FestivalError("Festival not found")
        return fest

    # ---------------- Lineup management ----------------
    def book_act(
        self,
        festival_id: int,
        stage_name: str,
        slot_index: int,
        band_id: int,
        payout_cents: int,
    ) -> None:
        fest = self.get_festival(festival_id)
        stage = fest.stages.get(stage_name)
        if not stage:
            raise FestivalError("Stage not found")
        try:
            slot = stage.slots[slot_index]
        except IndexError:  # pragma: no cover - defensive
            raise FestivalError("Invalid slot index") from None
        if slot.band_id is not None:
            raise BookingConflictError("Slot already booked")
        slot.band_id = band_id
        fest.finances["payouts"] += int(payout_cents)
        self.economy.deposit(band_id, int(payout_cents))

    # ---------------- Ticket sales ----------------
    def sell_tickets(
        self, festival_id: int, tier_name: str, qty: int, buyer_id: int
    ) -> int:
        fest = self.get_festival(festival_id)
        tier = next((t for t in fest.ticket_tiers if t.name == tier_name), None)
        if not tier:
            raise FestivalError("Ticket tier not found")
        qty = int(qty)
        if tier.sold + qty > tier.capacity:
            raise FestivalError("Not enough tickets available")
        tier.sold += qty
        revenue = tier.price_cents * qty
        fest.finances["revenue"] += revenue
        self.economy.deposit(fest.owner_id, revenue)
        try:
            self.legacy.log_milestone(
                fest.owner_id,
                "festival_revenue",
                f"Festival {festival_id} sold {qty} tickets",
                int(revenue // 100),
            )
        except Exception:
            pass
        for _ in range(qty):
            fest.tickets.append(
                Ticket(
                    band_id=None,
                    venue_id=festival_id,
                    price=tier.price_cents / 100.0,
                    type=tier.name,
                    fan_segment=None,
                    sold=True,
                )
            )
        return revenue

    # ---------------- Finance reporting ----------------
    def get_finances(self, festival_id: int) -> Dict[str, int]:
        fest = self.get_festival(festival_id)
        return dict(fest.finances)
