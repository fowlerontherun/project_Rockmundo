from fastapi import APIRouter, Depends

from auth.dependencies import require_permission
from backend.schemas.labels_schemas import (
    LabelCreateSchema,
    OfferRequestSchema,
    CounterOfferSchema,
    NegotiationSchema,
)
from services.contract_negotiation_service import ContractNegotiationService
from services.labels_service import (
    create_label as create_label_service,
    list_labels as list_labels_service,
    list_label_bands as list_label_bands_service,
)

router = APIRouter()
negotiation_service = ContractNegotiationService()


@router.post("/labels/create", dependencies=[Depends(require_permission(["admin", "moderator"]))])
def create_label(payload: LabelCreateSchema):
    return create_label_service(payload.name, payload.owner_id or 0)


@router.post("/labels/negotiations/offer", response_model=NegotiationSchema)
def offer_contract(payload: OfferRequestSchema):
    negotiation = negotiation_service.create_offer(
        payload.label_id, payload.band_id, payload.terms.dict()
    )
    return negotiation


@router.post("/labels/negotiations/{negotiation_id}/counter", response_model=NegotiationSchema)
def counter_offer(negotiation_id: int, payload: CounterOfferSchema):
    negotiation = negotiation_service.counter_offer(
        negotiation_id, payload.terms.dict()
    )
    return negotiation


@router.post("/labels/negotiations/{negotiation_id}/accept", response_model=NegotiationSchema)
def accept_offer(negotiation_id: int):
    negotiation = negotiation_service.accept_offer(negotiation_id)
    return negotiation


@router.get("/labels/list")
def list_labels():
    return list_labels_service()


@router.get("/labels/contracts/{label_id}")
def view_label_contracts(label_id: int):
    return list_label_bands_service(label_id)
