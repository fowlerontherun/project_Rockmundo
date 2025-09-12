"""Character API routes."""

from backend.auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from schemas.character import CharacterCreate, CharacterResponse
from schemas.avatar import AvatarUpdate
from services.avatar_service import AvatarService
from services.character_service import character_service
from utils.i18n import _

avatar_service = AvatarService()

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


class NetworkingUpdate(BaseModel):
    networking: int


@router.get(
    "/{character_id}/networking",
    dependencies=[Depends(require_permission(["admin", "player"]))],
)
def get_networking(
    character_id: int, user_id: int = Depends(get_current_user_id)
) -> dict[str, int]:
    avatar = avatar_service.get_avatar_by_character_id(character_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=_("Character not found"))
    return {"networking": avatar.networking}


@router.put(
    "/{character_id}/networking",
    dependencies=[Depends(require_permission(["admin", "player"]))],
)
def set_networking(
    character_id: int,
    payload: NetworkingUpdate,
    user_id: int = Depends(get_current_user_id),
) -> dict[str, int]:
    avatar = avatar_service.get_avatar_by_character_id(character_id)
    if not avatar:
        raise HTTPException(status_code=404, detail=_("Character not found"))
    updated = avatar_service.update_avatar(
        avatar.id, AvatarUpdate(networking=payload.networking)
    )
    assert updated  # for type checkers
    return {"networking": updated.networking}

