"""Routing stubs for skill learning sessions."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.learning_method import LearningMethod
from models.skill import Skill
from services.skill_service import SkillService

router = APIRouter(prefix="/learning", tags=["Learning"])
svc = SkillService()


class SessionRequest(BaseModel):
    user_id: int
    skill_id: int
    skill_name: str
    skill_category: str
    method: LearningMethod
    duration: int


class SpecializationRequest(BaseModel):
    user_id: int
    skill_id: int
    skill_name: str
    skill_category: str
    specialization: str


@router.post("/sessions")
def enqueue_session(payload: SessionRequest):
    """Enqueue a learning session (stub)."""
    skill = Skill(id=payload.skill_id, name=payload.skill_name, category=payload.skill_category)
    try:
        svc.train_with_method(payload.user_id, skill, payload.method, payload.duration)
    except ValueError as exc:  # pragma: no cover - stub handler
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "queued"}


@router.delete("/sessions/{session_id}")
def cancel_session(session_id: int):
    """Cancel a queued session (stub)."""
    return {"status": "cancelled", "session_id": session_id}


@router.post("/specializations")
def choose_specialization(payload: SpecializationRequest):
    """Select a specialization for a skill."""
    skill = Skill(
        id=payload.skill_id,
        name=payload.skill_name,
        category=payload.skill_category,
    )
    svc.select_specialization(payload.user_id, skill, payload.specialization)
    return {"status": "selected", "specialization": payload.specialization}


__all__ = ["router"]
