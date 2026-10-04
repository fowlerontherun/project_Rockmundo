"""Routing stubs for skill learning sessions."""

from fastapi import APIRouter, HTTPException, Depends
from auth.character_dependencies import get_current_character_id
from pydantic import BaseModel

from backend.models.learning_method import LearningMethod
from backend.models.skill import Skill
from services.skill_service import SkillService
from services.luthiery_progression import (
    SKILL_DESCRIPTIONS,
    learning_options_for,
    unlocks_for_level,
)
from seeds.skill_seed import SEED_SKILLS
from seeds.skill_seed import SEED_SKILLS, SKILL_NAME_TO_ID
from services.luthiery_progression import (
    SKILL_DESCRIPTIONS,
    learning_options_for,
    unlocks_for_level,
)

router = APIRouter(prefix="/learning", tags=["Learning"])
_SKILLS_BY_NAME = {skill.name: skill for skill in SEED_SKILLS}
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
def enqueue_session(payload: SessionRequest, character_id: int = Depends(get_current_character_id)):
    if payload.user_id != character_id:
        raise HTTPException(status_code=403, detail="Learning belongs to the selected character")
    """Enqueue a learning session (stub)."""
    skill = Skill(id=payload.skill_id, name=payload.skill_name, category=payload.skill_category)
    try:
        svc.train_with_method(character_id, skill, payload.method, payload.duration)
    except ValueError as exc:  # pragma: no cover - stub handler
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "queued"}


@router.delete("/sessions/{session_id}")
def cancel_session(session_id: int):
    """Cancel a queued session (stub)."""
    return {"status": "cancelled", "session_id": session_id}


@router.post("/specializations")
def choose_specialization(payload: SpecializationRequest, character_id: int = Depends(get_current_character_id)):
    if payload.user_id != character_id:
        raise HTTPException(status_code=403, detail="Skills belong to the selected character")
    """Select a specialization for a skill."""
    skill = Skill(
        id=payload.skill_id,
        name=payload.skill_name,
        category=payload.skill_category,
    )
    svc.select_specialization(character_id, skill, payload.specialization)
    return {"status": "selected", "specialization": payload.specialization}


@router.get("/luthiery/tree")
def luthiery_tree(character_id: int = Depends(get_current_character_id)):
    """Return selected-character Luthiery progression for the player skill UI."""

    nodes = []
    for seed in SEED_SKILLS:
        if seed.name not in SKILL_DESCRIPTIONS:
            continue
        level = svc.get_skill_level(character_id, seed)
        requirements = [
            {
                "skill": next(
                    (candidate.name for candidate in SEED_SKILLS if candidate.id == prereq_id),
                    str(prereq_id),
                ),
                "level": required,
                "met": svc.get_skill_level(
                    character_id,
                    next(candidate for candidate in SEED_SKILLS if candidate.id == prereq_id),
                ) >= required,
            }
            for prereq_id, required in seed.prerequisites.items()
        ]
        nodes.append(
            {
                "id": seed.id,
                "key": seed.name,
                "name": seed.name.replace("_", " ").title(),
                "category": seed.category,
                "level": level,
                "parent_id": seed.parent_id,
                "description": SKILL_DESCRIPTIONS[seed.name],
                "locked": any(not requirement["met"] for requirement in requirements),
                "requirements": requirements,
                "learning": [
                    {
                        "method": option.method,
                        "title": option.title,
                        "min_level": option.min_level,
                        "max_level": option.max_level,
                    }
                    for option in learning_options_for(seed.name)
                ],
                "rewards": unlocks_for_level(level) if seed.name == "luthiery" else None,
            }
        )
    return {"category": "craftsmanship", "root": SKILL_NAME_TO_ID["luthiery"], "skills": nodes}


@router.get("/luthiery/tree")
def luthiery_tree(character_id: int = Depends(get_current_character_id)):
    """Return server-authoritative Luthiery discovery/progression metadata."""
    nodes = []
    for name, description in SKILL_DESCRIPTIONS.items():
        skill = _SKILLS_BY_NAME[name]
        level = svc.get_skill_level(character_id, skill)
        missing = []
        for prereq_id, required in skill.prerequisites.items():
            prereq = next(item for item in SEED_SKILLS if item.id == prereq_id)
            actual = svc.get_skill_level(character_id, prereq)
            if actual < required:
                missing.append(
                    {"skill": prereq.name, "required_level": required, "current_level": actual}
                )
        nodes.append(
            {
                "id": skill.id,
                "key": name,
                "label": name.replace("_", " ").title(),
                "description": description,
                "level": level,
                "locked": bool(missing),
                "missing_requirements": missing,
                "learning_methods": sorted({option.method for option in learning_options_for(name)}),
            }
        )
    root_level = svc.get_skill_level(character_id, _SKILLS_BY_NAME["luthiery"])
    return {
        "category": "craftsmanship",
        "skills": nodes,
        "rewards": unlocks_for_level(root_level),
    }


__all__ = ["router"]
