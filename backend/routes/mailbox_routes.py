from fastapi import APIRouter
from services.mailbox_service import *

router = APIRouter()

@router.post("/mail/send", dependencies=[Depends(require_role(["admin", "moderator"]))])
def send_message(payload: dict):
    return send_mail(payload)

@router.get("/mail/inbox/{user_id}")
def inbox(user_id: int):
    return get_inbox(user_id)

@router.post("/mail/archive")
def archive(payload: dict):
    return archive_mail(payload)