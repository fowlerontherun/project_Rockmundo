from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from services.economy_service import EconomyService
from services.property_service import PropertyService, PropertyError


def require_role(roles):  # placeholder auth dependency
    async def _noop():
        return True
    return _noop

router = APIRouter(prefix="/properties", tags=["Properties"])
svc = PropertyService(economy=EconomyService())
svc.ensure_schema()


class PropertyPurchaseIn(BaseModel):
    owner_id: int
    name: str
    property_type: str
    location: str
    price_cents: int
    base_rent: int


class PropertyActionIn(BaseModel):
    owner_id: int


@router.post("/buy", dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))])
def buy_property(payload: PropertyPurchaseIn):
    try:
        pid = svc.buy_property(
            owner_id=payload.owner_id,
            name=payload.name,
            property_type=payload.property_type,
            location=payload.location,
            price_cents=payload.price_cents,
            base_rent=payload.base_rent,
        )
        return {"property_id": pid}
    except PropertyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upgrade/{property_id}", dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))])
def upgrade_property(property_id: int, payload: PropertyActionIn):
    try:
        return svc.upgrade_property(property_id, payload.owner_id)
    except PropertyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sell/{property_id}", dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))])
def sell_property(property_id: int, payload: PropertyActionIn):
    try:
        amount = svc.sell_property(property_id, payload.owner_id)
        return {"received_cents": amount}
    except PropertyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list/{owner_id}", dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))])
def list_properties(owner_id: int):
    return svc.list_properties(owner_id)
