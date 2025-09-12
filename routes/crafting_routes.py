from backend.auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict

from services.crafting_service import crafting_service, Recipe

router = APIRouter(prefix="/crafting", tags=["Crafting"])


class RecipePayload(BaseModel):
    name: str
    result_item_id: int
    components: Dict[int, int]


@router.post("/recipes", dependencies=[Depends(require_permission(["admin", "moderator"]))])
def add_recipe(payload: RecipePayload):
    recipe = Recipe(**payload.model_dump())
    crafting_service.add_recipe(recipe)
    return {"status": "created"}


@router.get("/recipes")
def list_recipes():
    return [crafting_service.asdict(r) for r in crafting_service.list_recipes()]


@router.post("/craft/{recipe_name}")
def craft_item(recipe_name: str, user_id: int = Depends(get_current_user_id)):
    try:
        crafting_service.craft(user_id, recipe_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "crafted"}
