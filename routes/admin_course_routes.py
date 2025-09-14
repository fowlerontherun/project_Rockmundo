"""Admin routes for managing courses."""
from fastapi import APIRouter, Depends, HTTPException, Request

from auth.dependencies import get_current_user_id, require_permission
from models.course import Course
from services.admin_audit_service import audit_dependency
from services.course_admin_service import course_admin_service, CourseAdminService
from pydantic import BaseModel

router = APIRouter(
    prefix="/courses", tags=["AdminCourses"], dependencies=[Depends(audit_dependency)]
)
svc: CourseAdminService = course_admin_service


class CourseIn(BaseModel):
    skill_target: str
    duration: int
    prerequisites: dict | None = None
    prestige: bool = False


@router.get("/")
async def list_courses(req: Request) -> list[Course]:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    return svc.list_courses()


@router.post("/")
async def create_course(payload: CourseIn, req: Request) -> Course:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    course = Course(id=0, **payload.dict())
    return svc.create_course(course)


@router.put("/{course_id}")
async def update_course(course_id: int, payload: CourseIn, req: Request) -> Course:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    try:
        return svc.update_course(course_id, **payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{course_id}")
async def delete_course(course_id: int, req: Request) -> dict[str, str]:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)
    svc.delete_course(course_id)
    return {"status": "deleted"}
