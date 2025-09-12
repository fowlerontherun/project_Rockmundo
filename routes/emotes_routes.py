from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter
from services.emotes_service import *
from schemas.emotes_schemas import EmoteTriggerSchema

router = APIRouter()

@router.post("/emotes/trigger", dependencies=[Depends(require_permission(["user", "band_member", "moderator", "admin"]))])
def trigger_emote(payload: EmoteTriggerSchema):
    return trigger_player_emote(payload.dict())

@router.get("/emotes/unlocked/")
def get_unlocked_emotes(user_id: int):
    return list_unlocked_emotes(user_id)