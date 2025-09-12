"""Admin routes for managing tutors."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from auth.dependencies import get_current_user_id, require_permission
from backend.models.tutor import Tutor
from services.admin_audit_service import audit_dependency
from services.tutor_admin_service import (
    TutorAdminService,
    get_tutor_admin_service,
)

router = APIRouter(
    prefix="/learning/tutors", tags=["AdminTutors"], dependencies=[Depends(audit_dependency)]
)
svc: TutorAdminService = get_tutor_admin_service()


class TutorIn(BaseModel):
    name: str
    specialization: str
    hourly_rate: int
    level_requirement: int


async def _ensure_admin(req: Request) -> None:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)


@router.get("/")
async def list_tutors(req: Request) -> list[Tutor]:
    await _ensure_admin(req)
    return svc.list_tutors()


@router.post("/")
async def create_tutor(payload: TutorIn, req: Request) -> Tutor:
    await _ensure_admin(req)
    tutor = Tutor(id=None, **payload.dict())
    return svc.create_tutor(tutor)


@router.put("/{tutor_id}")
async def update_tutor(tutor_id: int, payload: TutorIn, req: Request) -> Tutor:
    await _ensure_admin(req)
    try:
        return svc.update_tutor(tutor_id, **payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{tutor_id}")
async def delete_tutor(tutor_id: int, req: Request) -> dict[str, str]:
    await _ensure_admin(req)
    svc.delete_tutor(tutor_id)
    return {"status": "deleted"}


__all__ = [
    "router",
    "list_tutors",
    "create_tutor",
    "update_tutor",
    "delete_tutor",
    "TutorIn",
    "svc",
]
