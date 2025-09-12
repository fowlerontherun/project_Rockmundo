from fastapi import APIRouter, Depends

from backend.auth.dependencies import get_current_user_id
from services.notifications_service import NotificationsService


router = APIRouter(prefix="/user", tags=["User"])
svc = NotificationsService()


@router.get("/notifications")
def list_notifications(
    limit: int = 50,
    offset: int = 0,
    user_id: int = Depends(get_current_user_id),
):
    items = svc.list(user_id, limit=limit, offset=offset)
    return {"notifications": items, "unread": svc.unread_count(user_id)}


__all__ = ["router"]

