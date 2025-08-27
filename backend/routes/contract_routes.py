# Routes for contract negotiations.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.contract_negotiation_service import ContractNegotiationService

router = APIRouter(prefix="/contracts", tags=["Contracts"])

svc = ContractNegotiationService()
svc.economy.ensure_schema()


class OfferIn(BaseModel):
    label_id: int
    band_id: int
    terms: dict


class CounterIn(BaseModel):
    terms: dict


@router.post("/offer")
def create_offer(payload: OfferIn):
    negotiation = svc.create_offer(payload.label_id, payload.band_id, payload.terms)
    return negotiation.__dict__


@router.post("/{negotiation_id}/counter")
def counter_offer(negotiation_id: int, payload: CounterIn):
    try:
        negotiation = svc.counter_offer(negotiation_id, payload.terms)
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
