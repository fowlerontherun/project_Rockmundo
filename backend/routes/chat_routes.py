from schemas.chat_schemas import GroupMessageSchema, MessageSchema

from backend.auth.dependencies import get_current_user_id, require_permission  # noqa: F401
from backend.services.chat_service import (
    get_user_chat_history,
    send_group_chat,
    send_message,
)
from fastapi import APIRouter, Depends, HTTPException, Request  # noqa: F401

router = APIRouter()


@router.post(
    "/chat/send_direct",
    dependencies=[Depends(require_permission(["user", "band_member", "moderator", "admin"]))],
)
def send_direct_message(payload: MessageSchema):
    return send_message(payload.dict())


@router.post("/chat/send_group")
def send_group_message(payload: GroupMessageSchema):
    return send_group_chat(payload.dict())


@router.get("/chat/history/")
def get_chat_history(user_id: int):
    return get_user_chat_history(user_id)
