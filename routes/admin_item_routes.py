"""Admin routes for managing generic items."""
from fastapi import APIRouter, Depends, HTTPException, Request

from auth.dependencies import get_current_user_id, require_permission
from models.item import Item
from services.admin_audit_service import audit_dependency
from services.item_service import ItemService
from pydantic import BaseModel

router = APIRouter(
    prefix="/items", tags=["AdminItems"], dependencies=[Depends(audit_dependency)]
)
svc = ItemService()


class ItemIn(BaseModel):
    name: str
    category: str
    stats: dict[str, float] = {}


@router.get("/")
async def list_items(req: Request) -> list[Item]:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    return svc.list_items()


@router.post("/")
async def create_item(payload: ItemIn, req: Request) -> Item:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    item = Item(id=None, **payload.dict())
    return svc.create_item(item)


@router.put("/{item_id}")
async def update_item(item_id: int, payload: ItemIn, req: Request) -> Item:
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


class InventoryIn(BaseModel):
    quantity: int = 1


@router.post("/{item_id}/give/{user_id}")
async def give_item(item_id: int, user_id: int, payload: InventoryIn, req: Request) -> dict[str, str]:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    try:
        svc.add_to_inventory(user_id, item_id, payload.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "ok"}


@router.get("/inventory/{user_id}")
async def get_inventory(user_id: int, req: Request) -> dict[int, int]:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    return svc.get_inventory(user_id)
