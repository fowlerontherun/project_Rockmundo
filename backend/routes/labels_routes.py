from fastapi import APIRouter
from services.labels_service import *
from schemas.labels_schemas import LabelCreateSchema, ContractOfferSchema

router = APIRouter()

@router.post("/labels/create")
def create_label(payload: LabelCreateSchema):
    return create_music_label(payload.dict())

@router.post("/labels/offer_contract")
def offer_contract(payload: ContractOfferSchema):
    return offer_label_contract(payload.dict())

@router.get("/labels/list")
def list_labels():
    return get_all_labels()

@router.get("/labels/contracts/{band_id}")
def view_band_contracts(band_id: int):
    return get_contracts_for_band(band_id)