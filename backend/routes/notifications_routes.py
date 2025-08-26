# File: backend/routes/notifications_routes.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi import Depends
from auth.dependencies import get_current_user_id, require_role
from pydantic import BaseModel
from typing import Optional
from services.notifications_service import NotificationsService, NotificationsError

try:
    from auth.dependencies import require_role
except Exception:
    def require_role(roles, user_id: int = Depends(get_current_user_id)):
        async def _noop(user_id: int = Depends(get_current_user_id)):
            return True
        return _noop

router = APIRouter(prefix="/notifications", tags=["Notifications"])
svc = NotificationsService()
svc.ensure_schema()

class CreateNotificationIn(BaseModel):
    
    type: str
    title: str
    body: Optional[str] = ""
    link: Optional[str] = None

@router.post("", dependencies=[Depends(require_role(["admin","moderator"]))])
def create_notification(payload: CreateNotificationIn, user_id: int = Depends(get_current_user_id)):
    nid = svc.create_notification(**payload.model_dump())
    return {"id": nid}

@router.get("/unread/{user_id}", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def list_unread(user_id: int, limit: int = 50, offset: int = 0):
    return svc.list_unread(user_id, limit, offset)

@router.get("/recent/{user_id}", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def list_recent(user_id: int, limit: int = 50):
    return svc.list_recent(user_id, limit)

@router.post("/{notification_id}/read", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def mark_read(notification_id: int, user_id: int):
    svc.mark_read(notification_id, user_id)
    return {"ok": True}

@router.post("/read-all/{user_id}", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def mark_all_read(user_id: int):
    svc.mark_all_read(user_id)
    return {"ok": True}

@router.post("/{notification_id}/delete", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def delete(notification_id: int, user_id: int):
    svc.delete(notification_id, user_id)
    return {"ok": True}