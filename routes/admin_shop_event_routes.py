from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from auth.dependencies import get_current_user_id, require_permission
from services.admin_audit_service import audit_dependency
from services.event_service import list_shop_events, schedule_shop_event

router = APIRouter(
    prefix="/events/shop",
    tags=["AdminShopEvents"],
    dependencies=[Depends(audit_dependency)],
)


class ShopEventIn(BaseModel):
    name: str
    banner: str
    shop_id: int
    start_time: str
    end_time: str
    inventory: dict[int, int] | None = None
    price_modifier: float = 1.0


async def _ensure_admin(req: Request) -> None:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)


@router.get("/")
async def list_events(req: Request):
    await _ensure_admin(req)
    return list_shop_events()


@router.post("/")
async def create_event(payload: ShopEventIn, req: Request):
    await _ensure_admin(req)
    return schedule_shop_event(payload.dict())


__all__ = ["router", "ShopEventIn", "list_events", "create_event"]
