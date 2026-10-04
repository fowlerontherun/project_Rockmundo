"""REST routes for gear crafting and management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List

from auth.character_dependencies import get_current_character_id
from services.band_service import BandService
from services.gear_service import gear_service


router = APIRouter(prefix="/gear", tags=["Gear"])
_band_service = BandService()


def _require_band_member(band_id: int, character_id: int) -> None:
    """Reject attempts to control gear for another character's band."""
    info = _band_service.get_band_info(band_id)
    members = [] if not info else info.get("members", [])
    if character_id not in [member["user_id"] for member in members]:
        raise HTTPException(
            status_code=403,
            detail="Selected character is not a member of this band",
        )


def _require_item_owner_member(item_id: int, character_id: int) -> int:
    band_id = gear_service.owner_band_id(item_id)
    if band_id is None:
        raise HTTPException(status_code=404, detail="Gear item not found")
    _require_band_member(band_id, character_id)
    return band_id


class CraftIn(BaseModel):
    band_id: int
    base: str
    components: List[str]


@router.post("/craft")
def craft_item(
    payload: CraftIn,
    character_id: int = Depends(get_current_character_id),
):
    _require_band_member(payload.band_id, character_id)
    try:
        item = gear_service.craft(payload.base, payload.components)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not item:
        raise HTTPException(status_code=400, detail="Crafting failed")
    gear_service.assign_to_band(payload.band_id, item)
    return gear_service.asdict(item)


class RepairIn(BaseModel):
    amount: int


@router.post("/{item_id}/repair")
def repair_item(
    item_id: int,
    payload: RepairIn,
    character_id: int = Depends(get_current_character_id),
):
    _require_item_owner_member(item_id, character_id)
    item = gear_service.repair(item_id, payload.amount)
    return gear_service.asdict(item)


class TradeIn(BaseModel):
    item_id: int
    from_band: int
    to_band: int


@router.post("/trade")
def trade_item(
    payload: TradeIn,
    character_id: int = Depends(get_current_character_id),
):
    _require_band_member(payload.from_band, character_id)
    try:
        gear_service.trade(payload.item_id, payload.from_band, payload.to_band)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}


__all__ = ["router"]

