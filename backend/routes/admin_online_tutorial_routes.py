"""Admin routes for managing online tutorials."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user_id, require_role
from backend.models.online_tutorial import OnlineTutorial
from backend.services.admin_audit_service import audit_dependency
from backend.services.online_tutorial_admin_service import (
    OnlineTutorialAdminService,
    get_online_tutorial_admin_service,
)

router = APIRouter(
    prefix="/learning/tutorials",
    tags=["AdminTutorials"],
    dependencies=[Depends(audit_dependency)],
)
svc: OnlineTutorialAdminService = get_online_tutorial_admin_service()


class OnlineTutorialIn(BaseModel):
    video_url: str
    skill: str
    xp_rate: int
    plateau_level: int
    rarity_weight: int


async def _ensure_admin(req: Request) -> None:
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)


@router.get("/")
async def list_tutorials(req: Request) -> list[OnlineTutorial]:
    await _ensure_admin(req)
    return svc.list_tutorials()


@router.post("/")
async def create_tutorial(payload: OnlineTutorialIn, req: Request) -> OnlineTutorial:
    await _ensure_admin(req)
    tutorial = OnlineTutorial(id=None, **payload.dict())
    return svc.create_tutorial(tutorial)


@router.put("/{tutorial_id}")
async def update_tutorial(
    tutorial_id: int, payload: OnlineTutorialIn, req: Request
) -> OnlineTutorial:
    await _ensure_admin(req)
    try:
        return svc.update_tutorial(tutorial_id, **payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{tutorial_id}")
async def delete_tutorial(tutorial_id: int, req: Request) -> dict[str, str]:
    await _ensure_admin(req)
    svc.delete_tutorial(tutorial_id)
    return {"status": "deleted"}


__all__ = [
    "router",
    "list_tutorials",
    "create_tutorial",
    "update_tutorial",
    "delete_tutorial",
    "OnlineTutorialIn",
    "svc",
]
