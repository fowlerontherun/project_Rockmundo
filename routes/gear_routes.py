"""REST routes for gear crafting and management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from services.gear_service import gear_service


router = APIRouter(prefix="/gear", tags=["Gear"])


class CraftIn(BaseModel):
    band_id: int
    base: str
    components: List[str]


@router.post("/craft")
def craft_item(payload: CraftIn):
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
def repair_item(item_id: int, payload: RepairIn):
    item = gear_service.repair(item_id, payload.amount)
    return gear_service.asdict(item)


class TradeIn(BaseModel):
    item_id: int
    from_band: int
    to_band: int


@router.post("/trade")
def trade_item(payload: TradeIn):
    try:
        gear_service.trade(payload.item_id, payload.from_band, payload.to_band)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}


__all__ = ["router"]

