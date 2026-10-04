"""Routes for skill learning and Luthiery progression discovery."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.character_dependencies import get_current_character_id
from backend.models.learning_method import LearningMethod
from services.luthiery_progression import (
    SKILL_DESCRIPTIONS,
    learning_options_for,
    unlocks_for_level,
)
from services.skill_service import SkillService
from seeds.skill_seed import SEED_SKILLS

router = APIRouter(prefix="/learning", tags=["Learning"])
_SKILLS_BY_NAME = {skill.name: skill for skill in SEED_SKILLS}
_SKILLS_BY_ID = {skill.id: skill for skill in SEED_SKILLS}
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


def _canonical_skill(skill_id: int, name: str, category: str):
    skill = _SKILLS_BY_ID.get(skill_id)
    if not skill or skill.name != name or skill.category != category:
        raise HTTPException(status_code=400, detail="Unknown or mismatched skill")
    return skill


@router.post("/sessions")
def enqueue_session(
    payload: SessionRequest,
    character_id: int = Depends(get_current_character_id),
):
    """Train the selected character using a server-authoritative skill definition."""
    if payload.user_id != character_id:
        raise HTTPException(
            status_code=403,
            detail="Learning belongs to the selected character",
        )
    skill = _canonical_skill(
        payload.skill_id, payload.skill_name, payload.skill_category
    )
    try:
        svc.train_with_method(character_id, skill, payload.method, payload.duration)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "queued"}


@router.delete("/sessions/{session_id}")
def cancel_session(session_id: int):
    """Cancel a queued learning session."""
    return {"status": "cancelled", "session_id": session_id}


@router.post("/specializations")
def choose_specialization(
    payload: SpecializationRequest,
    character_id: int = Depends(get_current_character_id),
):
    if payload.user_id != character_id:
        raise HTTPException(
            status_code=403,
            detail="Skills belong to the selected character",
        )
    skill = _canonical_skill(
        payload.skill_id, payload.skill_name, payload.skill_category
    )
    svc.select_specialization(character_id, skill, payload.specialization)
    return {"status": "selected", "specialization": payload.specialization}


@router.get("/luthiery/tree")
def luthiery_tree(character_id: int = Depends(get_current_character_id)):
    """Return selected-character Luthiery progression for the player UI."""

    nodes = []
    for name, description in SKILL_DESCRIPTIONS.items():
        skill = _SKILLS_BY_NAME[name]
        level = svc.get_skill_level(character_id, skill)
        missing = []
        for prereq_id, required in skill.prerequisites.items():
            prereq = _SKILLS_BY_ID[prereq_id]
            actual = svc.get_skill_level(character_id, prereq)
            if actual < required:
                missing.append(
                    {
                        "skill": prereq.name,
                        "required_level": required,
                        "current_level": actual,
                    }
                )

        options = learning_options_for(name)
        nodes.append(
            {
                "id": skill.id,
                "key": name,
                "label": name.replace("_", " ").title(),
                "description": description,
                "level": level,
                "locked": bool(missing),
                "missing_requirements": missing,
                "learning_methods": sorted({option.method for option in options}),
                "learning_options": [
                    {
                        "method": option.method,
                        "title": option.title,
                        "min_level": option.min_level,
                        "max_level": option.max_level,
                    }
                    for option in options
                ],
            }
        )

    root_level = svc.get_skill_level(character_id, _SKILLS_BY_NAME["luthiery"])
    return {
        "category": "craftsmanship",
        "skills": nodes,
        "rewards": unlocks_for_level(root_level),
    }


__all__ = ["router"]
