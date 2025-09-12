"""Admin routes for economy configuration and auditing."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from auth.dependencies import get_current_user_id, require_permission
from services.economy_admin_service import EconomyAdminService
from backend.models.economy_config import EconomyConfig
from services.admin_audit_service import audit_dependency

router = APIRouter(
    prefix="/economy", tags=["AdminEconomy"], dependencies=[Depends(audit_dependency)]
)
svc = EconomyAdminService()


class ConfigUpdateIn(BaseModel):
    tax_rate: float | None = None
    inflation_rate: float | None = None
    payout_rate: int | None = None


@router.get("/config")
async def get_config(req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    return svc.get_config()


@router.put("/config")
async def update_config(payload: ConfigUpdateIn, req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    data = {k: v for k, v in payload.dict().items() if v is not None}
    try:
        return svc.update_config(**data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/config/preview")
async def preview_config(payload: ConfigUpdateIn, req: Request):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    current = svc.get_config()
    preview = current.__dict__.copy()
    for k, v in payload.dict().items():
        if v is not None:
            preview[k] = v
    return preview


@router.get("/transactions")
async def recent_transactions(req: Request, limit: int = 50):
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    return svc.recent_transactions(limit=limit)
