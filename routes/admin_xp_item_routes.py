"""Admin routes for managing XP items."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from auth.dependencies import get_current_user_id, require_permission
from backend.models.xp_item import XPItem
from services.admin_audit_service import audit_dependency
from services.xp_item_service import XPItemService

router = APIRouter(
    prefix="/xp/items", tags=["AdminXPItems"], dependencies=[Depends(audit_dependency)]
)
svc = XPItemService()


class XPItemIn(BaseModel):
    name: str
    effect_type: str = Field(pattern="^(flat|boost)$")
    amount: float
    duration: int


@router.get("/")
async def list_items(req: Request) -> list[XPItem]:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    return svc.list_items()


@router.post("/")
async def create_item(payload: XPItemIn, req: Request) -> XPItem:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    item = XPItem(id=None, **payload.dict())
    return svc.create_item(item)


@router.put("/{item_id}")
async def update_item(item_id: int, payload: XPItemIn, req: Request) -> XPItem:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    try:
        return svc.update_item(item_id, **payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{item_id}")
async def delete_item(item_id: int, req: Request) -> dict[str, str]:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    svc.delete_item(item_id)
    return {"status": "deleted"}
