from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.dependencies import get_current_user_id
from services.economy_service import EconomyService
from services.recording_service import RecordingService

router = APIRouter(prefix="/recording", tags=["recording"])
svc = RecordingService(economy=EconomyService())


class SessionCreate(BaseModel):
    studio: str
    start: str
    end: str
    tracks: List[int] = []
    cost_cents: int


class PersonnelAssign(BaseModel):
    user_id: int


class TrackUpdate(BaseModel):
    status: str


@router.post("/sessions")
def create_session(payload: SessionCreate, user_id: int = Depends(get_current_user_id)):
    try:
        session = svc.schedule_session(
            band_id=user_id,
            studio=payload.studio,
            start=payload.start,
            end=payload.end,
            tracks=payload.tracks,
            cost_cents=payload.cost_cents,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return session.to_dict()


@router.get("/sessions")
def list_sessions(user_id: int = Depends(get_current_user_id)):
    return [s.to_dict() for s in svc.list_sessions(band_id=user_id)]


@router.get("/sessions/{session_id}")
def get_session(session_id: int, user_id: int = Depends(get_current_user_id)):
    session = svc.get_session(session_id)
    if not session or session.band_id != user_id:
        raise HTTPException(status_code=404, detail="session_not_found")
    return session.to_dict()


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, user_id: int = Depends(get_current_user_id)):
    session = svc.get_session(session_id)
    if not session or session.band_id != user_id:
        raise HTTPException(status_code=404, detail="session_not_found")
    svc.delete_session(session_id)
    return {"ok": True}


@router.post("/sessions/{session_id}/personnel")
def assign_personnel(
    session_id: int, payload: PersonnelAssign, user_id: int = Depends(get_current_user_id)
):
    session = svc.get_session(session_id)
    if not session or session.band_id != user_id:
        raise HTTPException(status_code=404, detail="session_not_found")
    svc.assign_personnel(session_id, payload.user_id)
    return {"ok": True, "chemistry_avg": session.chemistry_avg}


@router.put("/sessions/{session_id}/tracks/{track_id}")
def update_track(
    session_id: int, track_id: int, payload: TrackUpdate, user_id: int = Depends(get_current_user_id)
):
    session = svc.get_session(session_id)
    if not session or session.band_id != user_id:
        raise HTTPException(status_code=404, detail="session_not_found")
    svc.update_track_status(session_id, track_id, payload.status)
    return {
        "ok": True,
        "track_statuses": session.track_statuses,
        "chemistry_avg": session.chemistry_avg,
    }
