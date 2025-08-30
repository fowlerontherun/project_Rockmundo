"""Admin routes for XP configuration."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user_id, require_role
from backend.services.xp_admin_service import XPAdminService
from backend.models.xp_config import XPConfig
from backend.services.admin_audit_service import audit_dependency

router = APIRouter(
    prefix="/xp", tags=["AdminXP"], dependencies=[Depends(audit_dependency)]
)
svc = XPAdminService()


class ConfigUpdateIn(BaseModel):
    daily_cap: int | None = None
    new_player_multiplier: float | None = None
    rested_xp_rate: float | None = None


@router.get("/config")
async def get_config(req: Request) -> XPConfig:
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    return svc.get_config()


@router.put("/config")
async def update_config(payload: ConfigUpdateIn, req: Request) -> XPConfig:
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    data = {k: v for k, v in payload.dict().items() if v is not None}
    try:
        return svc.update_config(**data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
