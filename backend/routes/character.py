"""Character API routes."""

from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Depends, HTTPException
from schemas.character import CharacterCreate, CharacterResponse
from services.character_service import character_service
from utils.i18n import _

router = APIRouter(prefix="/characters", tags=["Characters"])


@router.post(
    "/",
    response_model=CharacterResponse,
    dependencies=[Depends(require_permission(["admin", "player"]))],
)
def create_character(
    character: CharacterCreate, user_id: int = Depends(get_current_user_id)
):
    """Create a new character."""
    return character_service.create_character(character)


@router.get(
    "/{character_id}",
    response_model=CharacterResponse,
    dependencies=[Depends(require_permission(["admin", "player"]))],
)
def read_character(
    character_id: int, user_id: int = Depends(get_current_user_id)
):
    """Retrieve a single character by ID."""
    char = character_service.get_character(character_id)
    if not char:
        raise HTTPException(status_code=404, detail=_("Character not found"))
    return char


@router.get(
    "/",
    response_model=list[CharacterResponse],
    dependencies=[Depends(require_permission(["admin", "player"]))],
)
def list_characters(user_id: int = Depends(get_current_user_id)):
    """List all characters."""
    return character_service.list_characters()


@router.put(
    "/{character_id}",
    response_model=CharacterResponse,
    dependencies=[Depends(require_permission(["admin", "player"]))],
)
def update_character(
    character_id: int,
    character: CharacterCreate,
    user_id: int = Depends(get_current_user_id),
):
    """Update character information."""
    updated = character_service.update_character(character_id, character)
    if not updated:
        raise HTTPException(status_code=404, detail=_("Character not found"))
    return updated


@router.delete(
    "/{character_id}",
    dependencies=[Depends(require_permission(["admin", "player"]))],
)
def delete_character(
    character_id: int, user_id: int = Depends(get_current_user_id)
):
    """Delete a character."""
    deleted = character_service.delete_character(character_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=_("Character not found"))
    return {"ok": True}

