from fastapi import APIRouter, HTTPException, Depends
from auth.character_dependencies import get_current_character_id
from pydantic import BaseModel

from services.university_service import UniversityService

router = APIRouter(prefix="/university", tags=["University"])
svc = UniversityService()


class EnrollmentRequest(BaseModel):
    user_id: int
    course_id: int
    skill_level: int
    gpa: float


@router.get("/courses")
def list_courses():
    return [course.dict() for course in svc.list_courses()]


@router.post("/enroll")
def enroll(payload: EnrollmentRequest, character_id: int = Depends(get_current_character_id)):
    if payload.user_id != character_id:
        raise HTTPException(status_code=403, detail="Enrollment belongs to the selected character")
    try:
        svc.enroll(character_id, payload.course_id, payload.skill_level, payload.gpa)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "enrolled"}


__all__ = ["router"]
