from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.skill import Skill
from services.image_training_service import image_training_service

router = APIRouter(prefix="/training/image", tags=["ImageTraining"])


class TrainingPayload(BaseModel):
    user_id: int


@router.post("/workshop/{skill_name}", response_model=Skill)
def attend_image_workshop(skill_name: str, payload: TrainingPayload) -> Skill:
    """Attend an image workshop and gain XP."""

    try:
        return image_training_service.attend_workshop(payload.user_id, skill_name)
    except ValueError as exc:  # pragma: no cover - simple passthrough
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/course/{skill_name}", response_model=Skill)
def attend_image_course(skill_name: str, payload: TrainingPayload) -> Skill:
    """Attend an image course and gain XP."""

    try:
        return image_training_service.attend_course(payload.user_id, skill_name)
    except ValueError as exc:  # pragma: no cover - simple passthrough
        raise HTTPException(status_code=404, detail=str(exc))


__all__ = [
    "router",
    "attend_image_workshop",
    "attend_image_course",
    "TrainingPayload",
]

