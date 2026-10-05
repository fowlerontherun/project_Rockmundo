"""Character-safe Luthiery supplier and catalogue routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.character_dependencies import get_current_character_id
from seeds.skill_seed import SEED_SKILLS
from services.luthiery_catalogue_service import luthiery_catalogue_service
from services.luthiery_crafting_service import luthiery_crafting_service
from services.crafted_instrument_equipment_service import crafted_instrument_equipment
from services.skill_service import SkillService

router = APIRouter(prefix="/luthiery", tags=["Luthiery"])
_skill_service = SkillService()
_luthiery_skill = next(skill for skill in SEED_SKILLS if skill.name == "luthiery")


class InstrumentLock(BaseModel):
    locked: bool


class EquipInstrument(BaseModel):
    role: str | None = None


class MaterialPurchase(BaseModel):
    material_key: str
    quantity: int = 1


class CraftPart(BaseModel):
    material_key: str
    component_key: str | None = None


class CraftInstrument(BaseModel):
    request_token: str
    name: str
    instrument_type: str
    shape_key: str
    selections: dict[str, CraftPart]
    finish_key: str = "luthier.finish.solid"
    primary_colour: str = "#202020"
    accent_colour: str | None = None
    hardware_colour: str = "#c0c0c0"
    surface_sheen: str = "gloss"


def _level(character_id: int) -> int:
    return _skill_service.get_skill_level(character_id, _luthiery_skill)


@router.get("/catalogue")
def catalogue(character_id: int = Depends(get_current_character_id)):
    data = luthiery_catalogue_service.catalogue(_level(character_id))
    finishing = next(skill for skill in SEED_SKILLS if skill.name == "instrument_finishing")
    data["skill_levels"] = {"instrument_finishing": _skill_service.get_skill_level(character_id, finishing)}
    return data


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


@router.get("/crafted/inventory")
def crafted_inventory(character_id: int = Depends(get_current_character_id)):
    return {"items": luthiery_crafting_service.inventory(character_id)}


@router.post("/craft")
def craft_instrument(payload: CraftInstrument, character_id: int = Depends(get_current_character_id)):
    skill_names = ("luthiery", "woodworking", "fretwork", "instrument_electronics", "instrument_finishing")
    by_name = {skill.name: skill for skill in SEED_SKILLS}
    skills = {name: _skill_service.get_skill_level(character_id, by_name[name]) for name in skill_names}
    try:
        return luthiery_crafting_service.craft(
            character_id=character_id,
            request_token=payload.request_token,
            name=payload.name,
            instrument_type=payload.instrument_type,
            shape_key=payload.shape_key,
            selections={key: value.model_dump() for key, value in payload.selections.items()},
            skills=skills,
            finish_key=payload.finish_key,
            primary_colour=payload.primary_colour,
            accent_colour=payload.accent_colour,
            hardware_colour=payload.hardware_colour,
            surface_sheen=payload.surface_sheen,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/crafted/{item_id}")
def crafted_detail(item_id: int, character_id: int = Depends(get_current_character_id)):
    try:
        return luthiery_crafting_service.detail(character_id, item_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/crafted/{item_id}/lock")
def lock_instrument(payload: InstrumentLock, item_id: int, character_id: int = Depends(get_current_character_id)):
    try:
        return luthiery_crafting_service.set_locked(character_id, item_id, payload.locked)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/crafted/equipped")
def equipped_instrument(character_id: int = Depends(get_current_character_id)):
    return {"item": crafted_instrument_equipment.equipped(character_id)}


@router.post("/crafted/{item_id}/equip")
def equip_instrument(payload: EquipInstrument, item_id: int, character_id: int = Depends(get_current_character_id)):
    try:
        return crafted_instrument_equipment.equip(character_id, item_id, payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/crafted/equipped")
def unequip_instrument(character_id: int = Depends(get_current_character_id)):
    crafted_instrument_equipment.unequip(character_id)
    return {"ok": True}


@router.post("/crafted/{item_id}/maintain")
def maintain_instrument(item_id: int, character_id: int = Depends(get_current_character_id)):
    try:
        return crafted_instrument_equipment.repair(character_id, item_id, 25)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/crafted/{item_id}/rework")
def rework_instrument(item_id: int, character_id: int = Depends(get_current_character_id)):
    by_name = {skill.name: skill for skill in SEED_SKILLS}
    skills = {"luthiery": _skill_service.get_skill_level(character_id, by_name["luthiery"])}
    try:
        return luthiery_crafting_service.rework(character_id, item_id, skills)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


__all__ = ["router"]
