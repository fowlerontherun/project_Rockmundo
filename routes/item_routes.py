"""Routes for item interactions such as consuming drugs."""
from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_current_user_id, require_permission
from services.item_service import item_service

router = APIRouter(prefix="/items", tags=["Items"])


async def _current_user(user_id: int = Depends(get_current_user_id)) -> int:
    await require_permission(["user", "band_member", "moderator", "admin"], user_id)
    return user_id


@router.post("/consume-drug/{item_id}")
def consume_drug(item_id: int, user_id: int = Depends(_current_user)):
    try:
        return item_service.consume_drug(user_id, item_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
