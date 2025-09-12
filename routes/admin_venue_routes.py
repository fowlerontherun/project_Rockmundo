"""Administrative CRUD routes for venues."""
from fastapi import APIRouter, HTTPException, Request, Depends

from backend.auth.dependencies import get_current_user_id, require_permission
from services.venue_service import VenueService
from services.admin_audit_service import audit_dependency
from models.economy_config import set_config, EconomyConfig

router = APIRouter(
    prefix="/venues", tags=["AdminVenues"], dependencies=[Depends(audit_dependency)]
)
set_config(EconomyConfig())
svc = VenueService()


@router.post("/")
async def create_venue(payload: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    return svc.create_venue(
        owner_id=payload.get("owner_id"),
        name=payload.get("name", ""),
        city=payload.get("city", ""),
        country=payload.get("country", ""),
        capacity=int(payload.get("capacity", 0)),
        rental_cost=int(payload.get("rental_cost", 0)),
    )


@router.get("/")
async def list_venues(req: Request, owner_id: int | None = None):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    return svc.list_venues(owner_id)


@router.put("/{venue_id}")
async def edit_venue(venue_id: int, payload: dict, req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    venue = svc.update_venue(venue_id, payload)
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@router.delete("/{venue_id}")
async def delete_venue(venue_id: int, req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    if not svc.delete_venue(venue_id):
        raise HTTPException(status_code=404, detail="Venue not found")
    return {"status": "deleted"}
