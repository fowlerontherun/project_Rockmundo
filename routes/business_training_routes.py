from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.skill import Skill
from services.business_training_service import business_training_service

router = APIRouter(prefix="/training/business", tags=["BusinessTraining"])


class TrainingPayload(BaseModel):
    user_id: int


@router.post("/workshop/{skill_name}", response_model=Skill)
def attend_business_workshop(skill_name: str, payload: TrainingPayload) -> Skill:
    """Attend a business workshop and gain XP."""

    try:
        return business_training_service.attend_workshop(payload.user_id, skill_name)
    except ValueError as exc:  # pragma: no cover - simple passthrough
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/course/{skill_name}", response_model=Skill)
def attend_business_course(skill_name: str, payload: TrainingPayload) -> Skill:
    """Attend a business course and gain XP."""

    try:
        return business_training_service.attend_course(payload.user_id, skill_name)
    except ValueError as exc:  # pragma: no cover - simple passthrough
        raise HTTPException(status_code=404, detail=str(exc))


__all__ = [
    "router",
    "attend_business_workshop",
    "attend_business_course",
    "TrainingPayload",
]
