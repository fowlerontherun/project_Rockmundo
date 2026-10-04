"""Admin controls for the Luthiery Phase 2 catalogue."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.dependencies import get_current_user_id, require_permission
from services.luthiery_catalogue_service import luthiery_catalogue_service

router = APIRouter(prefix="/admin/luthiery", tags=["Admin Luthiery"])


async def _admin(user_id: int = Depends(get_current_user_id)) -> int:
    await require_permission(["admin"], user_id)
    return user_id


class EnabledUpdate(BaseModel):
    enabled: bool


@router.get("/catalogue")
def catalogue(_admin_id: int = Depends(_admin)):
    return luthiery_catalogue_service.admin_catalogue()


@router.put("/catalogue/{content_type}/{content_key}/enabled")
def set_enabled(
    content_type: str,
    content_key: str,
    payload: EnabledUpdate,
    _admin_id: int = Depends(_admin),
):
    try:
        luthiery_catalogue_service.set_enabled(content_type, content_key, payload.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok", "enabled": payload.enabled}
