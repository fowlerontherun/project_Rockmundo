# File: backend/routes/mail_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List

from services.mail_service import MailService
from core.errors import AppError

# Replace with your real auth dependency
try:
    from auth.dependencies import require_role, get_current_user_id
except Exception:  # dev fallback
    def require_role(roles):
        async def _noop():
            return True
        return _noop
    async def get_current_user_id():
        return 1

router = APIRouter(prefix="/mail", tags=["Mail"])
svc = MailService()

class ComposeIn(BaseModel):
    sender_id: int = Field(..., ge=1)
    recipient_ids: List[int] = Field(..., min_items=1, max_items=20)
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., max_length=10000)

class ReplyIn(BaseModel):
    thread_id: int
    sender_id: int
    body: str = Field(..., max_length=10000)

@router.post("/compose", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def compose(payload: ComposeIn):
    try:
        return svc.compose(
            sender_id=payload.sender_id,
            recipient_ids=payload.recipient_ids,
            subject=payload.subject,
            body=payload.body
        )
    except AppError as e:
        raise e.to_http()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reply", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def reply(payload: ReplyIn):
    try:
        return svc.reply(
            thread_id=payload.thread_id,
            sender_id=payload.sender_id,
            body=payload.body
        )
    except AppError as e:
        raise e.to_http()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threads")
def list_threads(user_id: int, limit: int = 25, offset: int = 0):
    return svc.list_threads(user_id=user_id, limit=limit, offset=offset)

@router.get("/thread/{thread_id}")
def get_thread(thread_id: int, user_id: int, mark_read: bool = True):
    try:
        return svc.get_thread(thread_id=thread_id, user_id=user_id, mark_read=mark_read)
    except AppError as e:
        raise e.to_http()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/badge")
async def unread_badge(user_id: int = Depends(get_current_user_id)):
    return svc.unread_badge(user_id)
