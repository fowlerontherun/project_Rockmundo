from fastapi import APIRouter
from services.emotes_service import *
from schemas.emotes_schemas import EmoteTriggerSchema

router = APIRouter()

@router.post("/emotes/trigger")
def trigger_emote(payload: EmoteTriggerSchema):
    return trigger_player_emote(payload.dict())

@router.get("/emotes/unlocked/{user_id}")
def get_unlocked_emotes(user_id: int):
    return list_unlocked_emotes(user_id)