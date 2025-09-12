"""Admin endpoints for managing lifestyle configuration."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from auth.dependencies import get_current_user_id, require_permission
from services.admin_audit_service import audit_dependency
from backend.config import lifestyle as lifestyle_config


router = APIRouter(
    prefix="/lifestyle", tags=["AdminLifestyle"], dependencies=[Depends(audit_dependency)]
)


class LifestyleConfigIn(BaseModel):
    decay: dict[str, float] | None = None
    modifier_thresholds: dict[str, dict[str, float]] | None = None


@router.get("/config")
async def get_config(req: Request) -> dict:
    """Return current lifestyle configuration."""

    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    return {
        "decay": lifestyle_config.DECAY,
        "modifier_thresholds": lifestyle_config.MODIFIER_THRESHOLDS,
    }


@router.put("/config")
async def update_config(payload: LifestyleConfigIn, req: Request) -> dict:
    """Update lifestyle configuration values."""

    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)

    if payload.decay:
        lifestyle_config.DECAY.update(payload.decay)

    if payload.modifier_thresholds:
        for key, values in payload.modifier_thresholds.items():
            if key in lifestyle_config.MODIFIER_THRESHOLDS:
                lifestyle_config.MODIFIER_THRESHOLDS[key].update(values)
            else:
                lifestyle_config.MODIFIER_THRESHOLDS[key] = values

    return {
        "decay": lifestyle_config.DECAY,
        "modifier_thresholds": lifestyle_config.MODIFIER_THRESHOLDS,
    }

