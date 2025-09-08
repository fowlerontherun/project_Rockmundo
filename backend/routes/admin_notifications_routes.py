"""Admin notification management routes."""

from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user_id, require_permission
from services.admin_notifications_service import AdminNotificationsService

router = APIRouter(prefix="/notifications", tags=["AdminNotifications"])
svc = AdminNotificationsService()


@router.get("")
async def list_notifications(
    limit: int = 100,
    offset: int = 0,
    admin_id: int = Depends(get_current_user_id),
):
    await require_permission(["admin"], admin_id)
    items = svc.list(limit=limit, offset=offset)
    return {"notifications": items, "unread": svc.unread_count()}


@router.post("")
async def create_notification(
    payload: dict,
    admin_id: int = Depends(get_current_user_id),
):
    await require_permission(["admin"], admin_id)
    message = payload.get("message", "")
    severity = payload.get("severity", "info")
    notif_id = svc.create(message, severity)
    return {"id": notif_id}


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    admin_id: int = Depends(get_current_user_id),
):
    await require_permission(["admin"], admin_id)
    if not svc.mark_read(notification_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    admin_id: int = Depends(get_current_user_id),
):
    await require_permission(["admin"], admin_id)
    if not svc.delete(notification_id):
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True}
