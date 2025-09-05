from typing import List

import backend.seeds.genre_seed as genre_seed
import backend.seeds.skill_seed as skill_seed

import backend.seeds.stage_equipment_seed as equipment_seed
from backend.auth.dependencies import get_current_user_id, require_permission
from backend.models.genre import Genre
from backend.models.skill import Skill
from backend.models.stage_equipment import StageEquipment
from backend.schemas.admin_music_schema import GenreSchema, SkillSchema, StageEquipmentSchema

from backend.auth.dependencies import get_current_user_id, require_permission
from backend.models.genre import Genre
from backend.models.skill import Skill
from backend.schemas.admin_music_schema import GenreSchema, SkillSchema

from backend.services.admin_audit_service import audit_dependency
from fastapi import APIRouter, Depends, Request

router = APIRouter(
    prefix="/music", tags=["AdminMusic"], dependencies=[Depends(audit_dependency)]
)


async def _ensure_admin(req: Request) -> None:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)


@router.get("/skills")
async def list_skills(req: Request) -> List[dict]:
    await _ensure_admin(req)
    return [s.__dict__ for s in skill_seed.SEED_SKILLS]


@router.put("/skills")
async def replace_skills(skills: List[SkillSchema], req: Request) -> dict:
    await _ensure_admin(req)
    skill_seed.SEED_SKILLS = [Skill(**s.dict()) for s in skills]
    skill_seed.SKILL_NAME_TO_ID = {s.name: s.id for s in skill_seed.SEED_SKILLS}
    return {"status": "updated", "count": len(skill_seed.SEED_SKILLS)}


@router.get("/genres")
async def list_genres(req: Request) -> List[dict]:
    await _ensure_admin(req)
    return [g.__dict__ for g in genre_seed.SEED_GENRES]


@router.put("/genres")
async def replace_genres(genres: List[GenreSchema], req: Request) -> dict:
    await _ensure_admin(req)
    genre_seed.SEED_GENRES = [Genre(**g.dict()) for g in genres]
    genre_seed.GENRE_NAME_TO_ID = {g.name: g.id for g in genre_seed.SEED_GENRES}
    return {"status": "updated", "count": len(genre_seed.SEED_GENRES)}


@router.get("/equipment")
async def list_equipment(req: Request) -> List[dict]:
    await _ensure_admin(req)
    return [e.__dict__ for e in equipment_seed.SEED_STAGE_EQUIPMENT]


@router.put("/equipment")
async def replace_equipment(
    equipment: List[StageEquipmentSchema], req: Request
) -> dict:
    await _ensure_admin(req)
    equipment_seed.SEED_STAGE_EQUIPMENT = [
        StageEquipment(**e.dict()) for e in equipment
    ]
    equipment_seed.STAGE_EQUIPMENT_NAME_TO_ID = {
        e.name: e.id for e in equipment_seed.SEED_STAGE_EQUIPMENT
    }
    return {
        "status": "updated",
        "count": len(equipment_seed.SEED_STAGE_EQUIPMENT),
    }

