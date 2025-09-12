from fastapi import APIRouter, Depends, HTTPException, Request  # noqa: F401
from schemas.chat_schemas import GroupMembershipSchema, GroupMessageSchema, MessageSchema

from backend.auth.dependencies import get_current_user_id, require_permission  # noqa: F401
from services.chat_service import (
    add_user_to_group,
    get_user_chat_history,
    send_group_chat,
    send_message,
)

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


@router.post("/chat/join_group")
def join_group(payload: GroupMembershipSchema):
    add_user_to_group(payload.group_id, payload.user_id)
    return {"status": "group_joined"}


@router.get("/chat/history/")
def get_chat_history(user_id: int):
    return get_user_chat_history(user_id)
