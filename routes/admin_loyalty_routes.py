"""Admin routes for configuring loyalty tiers."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user_id, require_permission
from services.loyalty_service import loyalty_service
from services.admin_audit_service import audit_dependency

router = APIRouter(
    prefix="/economy/loyalty",
    tags=["AdminLoyalty"],
    dependencies=[Depends(audit_dependency)],
)


class TierIn(BaseModel):
    name: str
    threshold: int
    discount: float


@router.get("/tiers")
async def list_tiers(req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    return loyalty_service.list_tiers()


@router.post("/tiers")
async def set_tier(payload: TierIn, req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    loyalty_service.set_tier(payload.name, payload.threshold, payload.discount)
    return {"status": "ok"}


@router.delete("/tiers/{name}")
async def delete_tier(name: str, req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    if not loyalty_service.delete_tier(name):
        raise HTTPException(status_code=404, detail="tier not found")
    return {"status": "ok"}
