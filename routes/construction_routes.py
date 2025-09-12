from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.dependencies import get_current_user_id, require_permission
from models.construction import Blueprint, BuildPhase
from services.construction_service import ConstructionService
from services.economy_service import EconomyService
from services.property_service import PropertyService
from services.venue_service import VenueService

router = APIRouter(prefix="/construction", tags=["Construction"])

econ = EconomyService()
prop_service = PropertyService(economy=econ)
venue_service = VenueService(economy=econ)
svc = ConstructionService(economy=econ, properties=prop_service, venues=venue_service)


class LandPurchaseIn(BaseModel):
    location: str
    size: int
    price: int


@router.post("/land", dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))])
def purchase_land(payload: LandPurchaseIn, owner_id: int = Depends(get_current_user_id)):
    try:
        parcel_id = svc.purchase_land(owner_id, payload.location, payload.size, payload.price)
        return {"parcel_id": parcel_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class PhaseIn(BaseModel):
    name: str
    duration: int


class DesignIn(BaseModel):
    parcel_id: int
    target_id: int
    target_type: str
    name: str
    cost: int
    phases: List[PhaseIn]
    upgrade_effect: Dict[str, int]


@router.post("/design", dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))])
def submit_design(payload: DesignIn, owner_id: int = Depends(get_current_user_id)):
    blueprint = Blueprint(
        name=payload.name,
        cost=payload.cost,
        phases=[BuildPhase(p.name, p.duration) for p in payload.phases],
        target_type=payload.target_type,
        upgrade_effect=payload.upgrade_effect,
    )
    try:
        task = svc.submit_design(payload.parcel_id, blueprint, owner_id, payload.target_id)
        return {
            "parcel_id": task.parcel_id,
            "blueprint": task.blueprint.name,
            "phase_index": task.phase_index,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/progress",
    dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))],
)
def progress() -> List[Dict[str, int]]:
    return svc.get_queue()
