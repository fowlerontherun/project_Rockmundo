from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user_id, require_role
from backend.services.economy_service import EconomyService, EconomyError
from backend.services.marketplace_service import MarketplaceService, MarketplaceError

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])

_economy = EconomyService()
_market = MarketplaceService(economy=_economy)
_market.ensure_schema()

async def _current_user(user_id: int = Depends(get_current_user_id)) -> int:
    await require_role(["user", "band_member", "moderator", "admin"], user_id)
    return user_id

class ListingIn(BaseModel):
    title: str
    description: str = ""
    starting_price_cents: int

@router.get("/listings")
def list_listings():
    return _market.list_active()

@router.post("/listings")
def create_listing(payload: ListingIn, user_id: int = Depends(_current_user)):
    listing_id = _market.create_listing(
        user_id, payload.title, payload.description, payload.starting_price_cents
    )
    return {"id": listing_id}

@router.get("/listings/{listing_id}")
def get_listing(listing_id: int):
    try:
        return _market.get_listing(listing_id)
    except MarketplaceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@router.delete("/listings/{listing_id}")
def delete_listing(listing_id: int, user_id: int = Depends(_current_user)):
    try:
        _market.delete_listing(listing_id, user_id)
    except MarketplaceError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "ok"}

class BidIn(BaseModel):
    amount_cents: int

@router.post("/listings/{listing_id}/bid")
def place_bid(listing_id: int, payload: BidIn, user_id: int = Depends(_current_user)):
    try:
        _market.place_bid(listing_id, user_id, payload.amount_cents)
    except MarketplaceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok"}

@router.post("/listings/{listing_id}/purchase")
def purchase(listing_id: int, user_id: int = Depends(_current_user)):
    try:
        _market.purchase(listing_id, user_id)
    except (MarketplaceError, EconomyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok"}
