"""Service handling contract negotiation flows with persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Column, Integer, create_engine
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Session, declarative_base, sessionmaker


from models.label_management_models import NegotiationStage
from models.record_contract import RecordContract, RoyaltyTier
from backend.services.economy_service import EconomyService
from backend.models.label_management_models import NegotiationStage
from backend.models.record_contract import RecordContract, RoyaltyTier
from services.economy_service import EconomyService

Base = declarative_base()


class NegotiationModel(Base):
    __tablename__ = "contract_negotiations"

    id = Column(Integer, primary_key=True, index=True)
    label_id = Column(Integer, nullable=False)
    band_id = Column(Integer, nullable=False)
    terms = Column(JSON, nullable=False)
    stage = Column(SqlEnum(NegotiationStage), nullable=False, default=NegotiationStage.OFFER)
    recoupable_cents = Column(Integer, default=0)
    recouped_cents = Column(Integer, default=0)


@dataclass
class NegotiationRecord:
    id: int
    label_id: int
    band_id: int
    terms: RecordContract
    stage: NegotiationStage
    recoupable_cents: int = 0
    recouped_cents: int = 0


class ContractNegotiationService:
    """Persisted negotiation tracking with economy integration."""

    def __init__(self, economy: Optional[EconomyService] = None, db_path: Optional[str] = None):
        self.economy = economy or EconomyService(db_path=db_path)
        path = db_path or self.economy.db_path
        self.engine = create_engine(f"sqlite:///{path}")
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False, future=True)
        Base.metadata.create_all(self.engine)

    # ------------------------------------------------------------------
    def create_offer(self, label_id: int, band_id: int, terms: Dict[str, Any]) -> NegotiationRecord:
        terms = self._validate_terms(terms)
        recoup = (
            int(terms.get("advance_cents", 0))
            + int(terms.get("recoupable_budgets_cents", 0))
            + int(terms.get("marketing_budget_cents", 0))
        )
        with self.SessionLocal() as session:
            model = NegotiationModel(
                label_id=label_id,
                band_id=band_id,
                terms=dict(terms),
                stage=NegotiationStage.OFFER,
                recoupable_cents=recoup,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_record(model)

    def counter_offer(self, negotiation_id: int, terms: Dict[str, Any]) -> NegotiationRecord:
        terms = self._validate_terms(terms)
        with self.SessionLocal() as session:
            model = self._get_model(session, negotiation_id)
            if model.stage == NegotiationStage.ACCEPTED:
                raise ValueError("Negotiation already accepted")
            model.terms = dict(terms)
            model.stage = NegotiationStage.COUNTER
            model.recoupable_cents = (
                int(terms.get("advance_cents", 0))
                + int(terms.get("recoupable_budgets_cents", 0))
                + int(terms.get("marketing_budget_cents", 0))
            )
            session.commit()
            session.refresh(model)
            return self._to_record(model)

    def accept_offer(self, negotiation_id: int) -> NegotiationRecord:
        with self.SessionLocal() as session:
            model = self._get_model(session, negotiation_id)
            if model.stage == NegotiationStage.ACCEPTED:
                raise ValueError("Negotiation already accepted")
            contract = self._parse_contract(model.terms)
            advance = contract.advance_cents
            if advance:
                self.economy.transfer(model.label_id, model.band_id, advance)
            model.stage = NegotiationStage.ACCEPTED
            session.commit()
            session.refresh(model)
            return self._to_record(model)

    def apply_royalty_payment(self, negotiation_id: int, amount_cents: int) -> NegotiationRecord:
        """Apply a royalty payment, automatically recouping advances."""
        with self.SessionLocal() as session:
            model = self._get_model(session, negotiation_id)
            if model.stage != NegotiationStage.ACCEPTED:
                raise ValueError("Negotiation not accepted")
            recoup_remaining = model.recoupable_cents - model.recouped_cents
            recoup_amount = min(amount_cents, recoup_remaining)
            if recoup_amount:
                # band pays label back
                self.economy.transfer(model.band_id, model.label_id, recoup_amount)
                model.recouped_cents += recoup_amount
            payout = amount_cents - recoup_amount
            if payout:
                self.economy.transfer(model.label_id, model.band_id, payout)
            session.commit()
            session.refresh(model)
            return self._to_record(model)

    # ------------------------------------------------------------------
    def _get_model(self, session: Session, negotiation_id: int) -> NegotiationModel:
        model = session.get(NegotiationModel, negotiation_id)
        if not model:
            raise ValueError("Negotiation not found")
        return model

    def _to_record(self, model: NegotiationModel) -> NegotiationRecord:
        contract = self._parse_contract(model.terms)
        return NegotiationRecord(
            id=model.id,
            label_id=model.label_id,
            band_id=model.band_id,
            terms=contract,
            stage=model.stage,
            recoupable_cents=model.recoupable_cents,
            recouped_cents=model.recouped_cents,
        )

    def _parse_contract(self, data: Dict[str, Any]) -> RecordContract:
        tiers = [RoyaltyTier(**t) for t in data.get("royalty_tiers", [])]
        return RecordContract(
            advance_cents=int(data.get("advance_cents", 0)),
            royalty_tiers=tiers,
            term_months=int(data.get("term_months", 0)),
            territory=data.get("territory", "worldwide"),
            recoupable_budgets_cents=int(data.get("recoupable_budgets_cents", 0)),
            options=list(data.get("options", [])),
            obligations=list(data.get("obligations", [])),
            marketing_budget_cents=int(data.get("marketing_budget_cents", 0)),
            distribution_fee_rate=float(data.get("distribution_fee_rate", 0.0)),
            rights_reversion_months=int(data.get("rights_reversion_months", 0)),
            release_commitment=int(data.get("release_commitment", 0)),
        )

    def _validate_terms(self, terms: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fill defaults for supported contract clauses."""
        validated = dict(terms)

        def _int(name: str, default: int = 0) -> None:
            try:
                value = int(validated.get(name, default))
                if value < 0:
                    raise ValueError
            except (TypeError, ValueError):
                value = default
            validated[name] = value

        def _float(name: str, default: float = 0.0) -> None:
            try:
                value = float(validated.get(name, default))
                if value < 0:
                    raise ValueError
            except (TypeError, ValueError):
                value = default
            validated[name] = value

        _int("advance_cents", 0)
        _int("recoupable_budgets_cents", 0)
        _int("marketing_budget_cents", 0)
        _float("distribution_fee_rate", 0.0)
        _int("rights_reversion_months", 0)
        _int("release_commitment", 0)

        return validated

    def _record_royalty_agreement(self, label_id: int, band_id: int, contract: RecordContract) -> None:
        """Placeholder hook for recording royalty agreements."""
        return None
