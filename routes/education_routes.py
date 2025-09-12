from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter
from schemas.education_schema import EducationSessionCreate, EducationSessionResponse
from datetime import date
from typing import List

router = APIRouter()
education_sessions = []
education_id_counter = 1

@router.post("/education/", response_model=EducationSessionResponse, dependencies=[Depends(require_permission(["user", "band_member", "moderator", "admin"]))])
def create_session(session: EducationSessionCreate):
    global education_id_counter
    new_session = session.dict()
    new_session.update({
        "id": education_id_counter,
        "start_date": date.today(),
        "completed": False
    })
    education_sessions.append(new_session)
    education_id_counter += 1
    return new_session

@router.get("/education/", response_model=List[EducationSessionResponse])
def list_sessions():
    return education_sessions