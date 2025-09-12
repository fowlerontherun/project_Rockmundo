"""Admin routes for managing XP multiplier events."""

from datetime import datetime

from auth.dependencies import get_current_user_id, require_permission
from backend.models.xp_event import XPEvent
from services.admin_audit_service import audit_dependency
from services.xp_event_service import XPEventService
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(
    prefix="/xp/events", tags=["AdminXPEvents"], dependencies=[Depends(audit_dependency)]
)
svc = XPEventService()


class XPEventIn(BaseModel):
    name: str
    start_time: datetime
    end_time: datetime
    multiplier: float
    skill_target: str | None = None


@router.get("/")
async def list_events(req: Request) -> list[XPEvent]:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    return svc.list_events()


@router.post("/")
async def create_event(payload: XPEventIn, req: Request) -> XPEvent:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    ev = XPEvent(id=None, **payload.dict())
    return svc.create_event(ev)


@router.put("/{event_id}")
async def update_event(event_id: int, payload: XPEventIn, req: Request) -> XPEvent:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    try:
        return svc.update_event(event_id, **payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{event_id}")
async def delete_event(event_id: int, req: Request) -> dict[str, str]:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    svc.delete_event(event_id)
    return {"status": "deleted"}
