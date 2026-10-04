from fastapi import APIRouter, Depends
from auth.dependencies import get_current_user_id
from auth.character_dependencies import get_current_character_id
from services.notifications_service import NotificationsService

router = APIRouter(prefix="/notification", tags=["notification"])
svc = NotificationsService()

@router.get("")
def list_notifications(user_id: int = Depends(get_current_user_id), character_id: int = Depends(get_current_character_id)):
    items = svc.list(user_id, character_id=character_id)
    svc.mark_all_read(user_id)
    return {"notifications": items}

@router.post("")
def create_notification(payload: dict, user_id: int = Depends(get_current_user_id), character_id: int = Depends(get_current_character_id)):
    title = payload.get("title", "")
    body = payload.get("body", "")
    type_ = payload.get("type", "system")
    notif_id = svc.create(user_id, title, body, type_, character_id=character_id if type_ != "system" else None)
    return {"id": notif_id}
