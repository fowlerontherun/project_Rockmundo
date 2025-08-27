"""Service handling contract negotiation flows."""

from __future__ import annotations

from typing import Dict, Any, Optional

from backend.models.label_management_models import (
    ContractNegotiation,
    NegotiationStage,
)
from backend.services.economy_service import EconomyService


class ContractNegotiationService:
    """In-memory negotiation tracking with economy integration."""

    def __init__(self, economy: Optional[EconomyService] = None):
        self.economy = economy or EconomyService()
        self.negotiations: Dict[int, ContractNegotiation] = {}
        self._next_id = 1

    def create_offer(self, label_id: int, band_id: int, terms: Dict[str, Any]) -> ContractNegotiation:
        negotiation = ContractNegotiation(
            id=self._next_id,
            label_id=label_id,
            band_id=band_id,
            terms=dict(terms),
            stage=NegotiationStage.OFFER,
        )
        self.negotiations[self._next_id] = negotiation
        self._next_id += 1
        return negotiation

    def counter_offer(self, negotiation_id: int, terms: Dict[str, Any]) -> ContractNegotiation:
        negotiation = self._get(negotiation_id)
        if negotiation.stage == NegotiationStage.ACCEPTED:
            raise ValueError("Negotiation already accepted")
        negotiation.terms = dict(terms)
        negotiation.stage = NegotiationStage.COUNTER
        return negotiation

    def accept_offer(self, negotiation_id: int) -> ContractNegotiation:
        negotiation = self._get(negotiation_id)
        if negotiation.stage == NegotiationStage.ACCEPTED:
            raise ValueError("Negotiation already accepted")
        advance = int(negotiation.terms.get("advance_cents", 0))
        royalty = float(negotiation.terms.get("royalty_rate", 0))
        # move advance funds
        if advance:
            self.economy.transfer(negotiation.label_id, negotiation.band_id, advance)
        # record royalty agreement as zero-amount transaction
        self._record_royalty_agreement(negotiation.label_id, negotiation.band_id, royalty)
        negotiation.stage = NegotiationStage.ACCEPTED
        return negotiation

    # internal helpers -------------------------------------------------
    def _get(self, negotiation_id: int) -> ContractNegotiation:
        negotiation = self.negotiations.get(negotiation_id)
        if not negotiation:
            raise ValueError("Negotiation not found")
        return negotiation

    def _record_royalty_agreement(self, label_id: int, band_id: int, rate: float) -> None:
        import sqlite3

        with sqlite3.connect(self.economy.db_path) as conn:
            cur = conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            src_id = self.economy._require_account(cur, label_id, "USD")
            dest_id = self.economy._require_account(cur, band_id, "USD")
            cur.execute(
                "INSERT INTO transactions (type, amount_cents, currency, src_account_id, dest_account_id) VALUES ('royalty', 0, 'USD', ?, ?)",
                (src_id, dest_id),
            )
            tid = cur.lastrowid
            cur.execute(
                "SELECT balance_cents FROM accounts WHERE id = ?",
                (src_id,),
            )
            src_balance = int(cur.fetchone()[0])
            cur.execute(
                "INSERT INTO ledger_entries (account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, 0, ?)",
                (src_id, tid, src_balance),
            )
            cur.execute(
                "SELECT balance_cents FROM accounts WHERE id = ?",
                (dest_id,),
            )
            dest_balance = int(cur.fetchone()[0])
            cur.execute(
                "INSERT INTO ledger_entries (account_id, transaction_id, delta_cents, balance_after) VALUES (?, ?, 0, ?)",
                (dest_id, tid, dest_balance),
            )
            conn.commit()
