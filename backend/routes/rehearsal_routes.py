"""API routes for rehearsal scheduling and attendance."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from services.rehearsal_service import RehearsalService


router = APIRouter(prefix="/rehearsals", tags=["Rehearsals"])
svc = RehearsalService()


class RehearsalIn(BaseModel):
    band_id: int
    start: str
    end: str
    attendees: List[int] = []


@router.post("/")
def schedule_rehearsal(payload: RehearsalIn):
    try:
        return svc.book_session(
            band_id=payload.band_id,
            start=payload.start,
            end=payload.end,
            attendees=payload.attendees,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class AttendanceIn(BaseModel):
    member_id: int


@router.post("/{rehearsal_id}/attendance")
def mark_attendance(rehearsal_id: int, payload: AttendanceIn):
    svc.record_attendance(rehearsal_id, payload.member_id)
    return {"rehearsal_id": rehearsal_id, "member_id": payload.member_id}


@router.get("/{rehearsal_id}/attendance")
def get_attendance(rehearsal_id: int):
    return svc.attendance(rehearsal_id)


__all__ = ["router"]

