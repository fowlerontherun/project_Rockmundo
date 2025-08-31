# Routes for contract negotiations.

from fastapi import APIRouter, HTTPException

from backend.services.contract_negotiation_service import ContractNegotiationService
from pydantic import BaseModel, Field

router = APIRouter(prefix="/contracts", tags=["Contracts"])

svc = ContractNegotiationService()
svc.economy.ensure_schema()


class ContractTerms(BaseModel):
    """Supported negotiable clauses."""

    advance_cents: int = Field(0, description="Upfront payment to the band")
    royalty_rate: float = Field(0.0, description="Revenue percentage for the band")
    marketing_budget_cents: int = Field(0, description="Label-funded marketing spend")
    distribution_fee_rate: float = Field(0.0, description="Percentage fee for distribution services")
    rights_reversion_months: int = Field(0, description="Months until rights revert to the band")
    release_commitment: int = Field(0, description="Minimum releases label commits to")


class OfferIn(BaseModel):
    label_id: int
    band_id: int
    terms: ContractTerms


class CounterIn(BaseModel):
    terms: ContractTerms


@router.post("/offer")
def create_offer(payload: OfferIn):
    negotiation = svc.create_offer(payload.label_id, payload.band_id, payload.terms.dict())
    return negotiation.__dict__


@router.post("/{negotiation_id}/counter")
def counter_offer(negotiation_id: int, payload: CounterIn):
    try:
        negotiation = svc.counter_offer(negotiation_id, payload.terms.dict())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return negotiation.__dict__


@router.post("/{negotiation_id}/accept")
def accept_offer(negotiation_id: int):
    try:
        negotiation = svc.accept_offer(negotiation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return negotiation.__dict__
