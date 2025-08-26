from fastapi import APIRouter
from fastapi import Depends
from auth.dependencies import get_current_user_id, require_role
from services.mailbox_service import *

router = APIRouter()

@router.post("/mail/send", dependencies=[Depends(require_role(["admin", "moderator"]))])
def send_message(payload: dict, user_id: int = Depends(get_current_user_id)):
    return send_mail(payload)

@router.get("/mail/inbox")
def inbox(user_id: int = Depends(get_current_user_id)):
    return get_inbox(user_id)

@router.post("/mail/archive")
def archive(payload: dict, user_id: int = Depends(get_current_user_id)):
    return archive_mail(payload)