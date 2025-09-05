"""Admin routes for managing apprenticeships."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user_id, require_permission
from backend.models.apprenticeship import Apprenticeship
from backend.services.admin_audit_service import audit_dependency
from backend.services.apprenticeship_admin_service import (
    ApprenticeshipAdminService,
    get_apprenticeship_admin_service,
)

router = APIRouter(
    prefix="/learning/mentors", tags=["AdminApprenticeships"], dependencies=[Depends(audit_dependency)]
)
svc: ApprenticeshipAdminService = get_apprenticeship_admin_service()


class ApprenticeshipIn(BaseModel):
    student_id: int
    mentor_id: int
    mentor_type: str
    skill_id: int
    duration_days: int
    level_requirement: int
    start_date: str | None = None
    status: str = "pending"


async def _ensure_admin(req: Request) -> None:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)


@router.get("/")
async def list_apprenticeships(req: Request) -> list[Apprenticeship]:
    await _ensure_admin(req)
    return svc.list_apprenticeships()


@router.post("/")
async def create_apprenticeship(payload: ApprenticeshipIn, req: Request) -> Apprenticeship:
    await _ensure_admin(req)
    app = Apprenticeship(id=None, **payload.dict())
    return svc.create_apprenticeship(app)


@router.put("/{app_id}")
async def update_apprenticeship(app_id: int, payload: ApprenticeshipIn, req: Request) -> Apprenticeship:
    await _ensure_admin(req)
    try:
        return svc.update_apprenticeship(app_id, **payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{app_id}")
async def delete_apprenticeship(app_id: int, req: Request) -> dict[str, str]:
    await _ensure_admin(req)
    svc.delete_apprenticeship(app_id)
    return {"status": "deleted"}


__all__ = [
    "router",
    "list_apprenticeships",
    "create_apprenticeship",
    "update_apprenticeship",
    "delete_apprenticeship",
    "ApprenticeshipIn",
    "svc",
]
