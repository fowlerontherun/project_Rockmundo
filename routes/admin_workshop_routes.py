"""Admin routes for managing workshop events."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from auth.dependencies import get_current_user_id, require_permission
from backend.models.workshop import Workshop
from services.admin_audit_service import audit_dependency
from services.workshop_admin_service import (
    WorkshopAdminService,
    get_workshop_admin_service,
)

router = APIRouter(
    prefix="/learning/workshops",
    tags=["AdminWorkshops"],
    dependencies=[Depends(audit_dependency)],
)
svc: WorkshopAdminService = get_workshop_admin_service()


class WorkshopIn(BaseModel):
    skill_target: str
    xp_reward: int
    ticket_price: int
    schedule: str


async def _ensure_admin(req: Request) -> None:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)


@router.get("/")
async def list_workshops(req: Request) -> list[Workshop]:
    await _ensure_admin(req)
    return svc.list_workshops()


@router.post("/")
async def create_workshop(payload: WorkshopIn, req: Request) -> Workshop:
    await _ensure_admin(req)
    ws = Workshop(id=None, **payload.dict())
    return svc.create_workshop(ws)


@router.put("/{workshop_id}")
async def update_workshop(workshop_id: int, payload: WorkshopIn, req: Request) -> Workshop:
    await _ensure_admin(req)
    try:
        return svc.update_workshop(workshop_id, **payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{workshop_id}")
async def delete_workshop(workshop_id: int, req: Request) -> dict[str, str]:
    await _ensure_admin(req)
    svc.delete_workshop(workshop_id)
    return {"status": "deleted"}


__all__ = [
    "router",
    "list_workshops",
    "create_workshop",
    "update_workshop",
    "delete_workshop",
    "WorkshopIn",
    "svc",
]
