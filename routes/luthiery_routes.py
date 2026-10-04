"""Character-safe Luthiery supplier and catalogue routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.character_dependencies import get_current_character_id
from seeds.skill_seed import SEED_SKILLS
from services.luthiery_catalogue_service import luthiery_catalogue_service
from services.skill_service import SkillService

router = APIRouter(prefix="/luthiery", tags=["Luthiery"])
_skill_service = SkillService()
_luthiery_skill = next(skill for skill in SEED_SKILLS if skill.name == "luthiery")


class MaterialPurchase(BaseModel):
    material_key: str
    quantity: int = 1


def _level(character_id: int) -> int:
    return _skill_service.get_skill_level(character_id, _luthiery_skill)


@router.get("/catalogue")
def catalogue(character_id: int = Depends(get_current_character_id)):
    return luthiery_catalogue_service.catalogue(_level(character_id))


@router.get("/materials/inventory")
def material_inventory(character_id: int = Depends(get_current_character_id)):
    return {"items": luthiery_catalogue_service.inventory(character_id)}


@router.post("/supplier/purchase")
def purchase_material(
    payload: MaterialPurchase,
    character_id: int = Depends(get_current_character_id),
):
    try:
        return luthiery_catalogue_service.purchase(
            character_id,
            payload.material_key,
            payload.quantity,
            _level(character_id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


__all__ = ["router"]
