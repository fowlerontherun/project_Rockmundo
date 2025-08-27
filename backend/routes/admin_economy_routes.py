"""Admin routes for economy configuration and auditing."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from auth.dependencies import get_current_user_id, require_role
from services.economy_admin_service import EconomyAdminService
from models.economy_config import EconomyConfig

router = APIRouter(prefix="/economy", tags=["AdminEconomy"])
svc = EconomyAdminService()


class ConfigUpdateIn(BaseModel):
    tax_rate: float | None = None
    inflation_rate: float | None = None
    payout_rate: int | None = None


@router.get("/config")
async def get_config(req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    return svc.get_config()


@router.put("/config")
async def update_config(payload: ConfigUpdateIn, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    data = {k: v for k, v in payload.dict().items() if v is not None}
    try:
        return svc.update_config(**data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/config/preview")
async def preview_config(payload: ConfigUpdateIn, req: Request):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    current = svc.get_config()
    preview = current.__dict__.copy()
    for k, v in payload.dict().items():
        if v is not None:
            preview[k] = v
    return preview


@router.get("/transactions")
async def recent_transactions(req: Request, limit: int = 50):
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)
    return svc.recent_transactions(limit=limit)
