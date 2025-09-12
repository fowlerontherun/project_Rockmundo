from fastapi import APIRouter, Depends, HTTPException

from backend.auth.dependencies import get_current_user_id
from services.notifications_service import NotificationsService

router = APIRouter(prefix="/notifications", tags=["Notifications"])
svc = NotificationsService()


@router.get("")
def list_notifications(
    limit: int = 50,
    offset: int = 0,
    user_id: int = Depends(get_current_user_id),
):
    """Return notifications for the current user with pagination."""
    items = svc.list(user_id, limit=limit, offset=offset)
    return {"notifications": items, "unread": svc.unread_count(user_id)}


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, user_id: int = Depends(get_current_user_id)):
    if not svc.mark_read(notification_id, user_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True}


@router.post("/read-all")
def mark_all_read(user_id: int = Depends(get_current_user_id)):
    return {"marked": svc.mark_all_read(user_id)}
