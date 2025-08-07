from fastapi import APIRouter
from services.chat_service import *
from schemas.chat_schemas import MessageSchema, GroupMessageSchema

router = APIRouter()

@router.post("/chat/send_direct")
def send_direct_message(payload: MessageSchema):
    return send_message(payload.dict())

@router.post("/chat/send_group")
def send_group_message(payload: GroupMessageSchema):
    return send_group_chat(payload.dict())

@router.get("/chat/history/{user_id}")
def get_chat_history(user_id: int):
    return get_user_chat_history(user_id)