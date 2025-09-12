"""Routes for managing skill apprenticeships."""

from fastapi import APIRouter
from pydantic import BaseModel

from services.apprenticeship_service import ApprenticeshipService
from services.karma_service import KarmaService
from services.karma_db import KarmaDB



router = APIRouter(prefix="/apprenticeships", tags=["Apprenticeships"])
svc = ApprenticeshipService(karma=KarmaService(KarmaDB()))


class RequestIn(BaseModel):
    student_id: int
    mentor_id: int
    mentor_type: str = "player"
    skill_id: int
    duration_days: int


@router.post("/request")
def request_apprenticeship(payload: RequestIn):
    app = svc.request(
        payload.student_id,
        payload.mentor_id,
        payload.mentor_type,
        payload.skill_id,
        payload.duration_days,
    )
    return app.to_dict()


class AcceptIn(BaseModel):
    apprenticeship_id: int


@router.post("/accept")
def accept_apprenticeship(payload: AcceptIn):
    svc.start(payload.apprenticeship_id)
    return {"status": "started"}


class CompleteIn(BaseModel):
    apprenticeship_id: int
    mentor_level: int
    relationship: int


@router.post("/complete")
def complete_apprenticeship(payload: CompleteIn):
    xp = svc.stop(payload.apprenticeship_id, payload.mentor_level, payload.relationship)
    return {"xp": xp}


__all__ = ["router"]
