from fastapi import APIRouter
from services.replay_service import *

router = APIRouter()

@router.post("/replay/log", dependencies=[Depends(require_role(["admin"]))])
def log_event(payload: dict):
    return log_player_event(payload)

@router.get("/replay/history/{user_id}")
def get_replay_history(user_id: int):
    return get_player_replay_history(user_id)

@router.get("/replay/event/{user_id}/{event_id}")
def get_specific_replay(user_id: int, event_id: str):
    return get_replay_detail(user_id, event_id)