from fastapi import APIRouter

from services.perk_service import perk_service

router = APIRouter()


@router.get("/avatar/{user_id}/perks")
def list_perks(user_id: int) -> list[dict]:
    """Return perks unlocked for the given user."""

    perks = perk_service.get_perks(user_id)
    return [
        {"id": p.id, "name": p.name, "description": p.description}
        for p in perks
    ]
