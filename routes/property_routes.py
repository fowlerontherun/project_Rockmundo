from services.achievement_service import AchievementService
from services.economy_service import EconomyService
from services.property_service import PropertyError, PropertyService

from backend.auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/properties", tags=["Properties"])
_achievements = AchievementService()
svc = PropertyService(economy=EconomyService(), achievements=_achievements)
svc.ensure_schema()


class PropertyPurchaseIn(BaseModel):
    name: str
    property_type: str
    location: str
    price_cents: int
    base_rent: int


@router.post("/buy", dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))])
def buy_property(
    payload: PropertyPurchaseIn, owner_id: int = Depends(get_current_user_id)
):
    try:
        pid = svc.buy_property(
            owner_id=owner_id,
            name=payload.name,
            property_type=payload.property_type,
            location=payload.location,
            price_cents=payload.price_cents,
            base_rent=payload.base_rent,
        )
        return {"property_id": pid}
    except PropertyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/upgrade/{property_id}",
    dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))],
)
def upgrade_property(property_id: int, owner_id: int = Depends(get_current_user_id)):
    try:
        return svc.upgrade_property(property_id, owner_id)
    except PropertyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/rent/{property_id}",
    dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))],
)
def rent_property(property_id: int, renter_id: int = Depends(get_current_user_id)):
    try:
        return svc.rent_property(property_id, renter_id)
    except PropertyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/sell/{property_id}",
    dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))],
)
def sell_property(property_id: int, owner_id: int = Depends(get_current_user_id)):
    try:
        amount = svc.sell_property(property_id, owner_id)
        return {"received_cents": amount}
    except PropertyError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list", dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))])
def list_properties(owner_id: int = Depends(get_current_user_id)):
    return svc.list_properties(owner_id)
