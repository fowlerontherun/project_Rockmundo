# File: backend/routes/mail_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from services.mail_service import MailService, MailError

try:
    from auth.dependencies import require_role
except Exception:
    def require_role(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/mail", tags=["Mail"])
svc = MailService()
svc.ensure_schema()

class ComposeIn(BaseModel):
    sender_id: int
    recipient_ids: List[int]
    subject: str
    body: str

class ReplyIn(BaseModel):
    thread_id: int
    sender_id: int
    body: str

@router.post("/compose", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def compose(payload: ComposeIn):
    try:
        tid = svc.start_thread(payload.sender_id, payload.recipient_ids, payload.subject, payload.body)
        return {"thread_id": tid}
    except MailError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reply", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def reply(payload: ReplyIn):
    try:
        mid = svc.reply(payload.thread_id, payload.sender_id, payload.body)
        return {"message_id": mid}
    except MailError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/inbox/{user_id}", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def inbox(user_id: int, include_archived: bool = False, limit: int = 50, offset: int = 0):
    return svc.list_inbox(user_id, include_archived, limit, offset)

@router.get("/sent/{user_id}", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def sent(user_id: int, limit: int = 50, offset: int = 0):
    return svc.list_sent(user_id, limit, offset)

@router.get("/thread/{thread_id}", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def get_thread(thread_id: int, user_id: int):
    try:
        return svc.get_thread(thread_id, user_id)
    except MailError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/thread/{thread_id}/read", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def mark_read(thread_id: int, user_id: int):
    svc.mark_read(thread_id, user_id)
    return {"ok": True}

@router.post("/thread/{thread_id}/archive", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def archive(thread_id: int, user_id: int, archived: bool = True):
    svc.archive(thread_id, user_id, archived)
    return {"ok": True}

@router.post("/thread/{thread_id}/delete", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def delete_for_user(thread_id: int, user_id: int):
    svc.delete_for_user(thread_id, user_id)
    return {"ok": True}
