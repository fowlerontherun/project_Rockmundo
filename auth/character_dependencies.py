"""Dependencies for resolving character-scoped gameplay state."""

from fastapi import Depends, Header, HTTPException, status

from auth.dependencies import get_current_user_id
from services.character_service import character_service


async def get_current_character_id(
    user_id: int = Depends(get_current_user_id),
    x_character_id: int | None = Header(default=None, alias="X-Character-ID"),
) -> int:
    """Return a character owned by the authenticated account.

    Character-scoped APIs must use this dependency instead of trusting a user
    or character id supplied in the request body/path. During the transition,
    accounts with exactly one character may omit the header.
    """
    characters = character_service.list_characters(user_id)
    if x_character_id is None:
        if len(characters) == 1:
            return int(characters[0]["id"])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CHARACTER_REQUIRED",
                "message": "Select a character before accessing character-specific data.",
            },
        )
    if not character_service.owns_character(user_id, x_character_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CHARACTER_NOT_FOUND", "message": "Character not found."},
        )
    return x_character_id
