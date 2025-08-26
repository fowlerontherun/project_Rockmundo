from fastapi import APIRouter
from fastapi import Depends
from auth.dependencies import get_current_user_id, require_role
from services.scheduler_service import *

router = APIRouter()

@router.post("/notify/send", dependencies=[Depends(require_role(["user", "band_member", "moderator", "admin"]))])
def send_notification(payload: dict, user_id: int = Depends(get_current_user_id)):
    return send_user_notification(payload)

@router.post("/scheduler/schedule_event")
def schedule_event(payload: dict, user_id: int = Depends(get_current_user_id)):
    return schedule_game_event(payload)

@router.get("/scheduler/upcoming"\)"
def get_upcoming_events(user_id: int):
    return fetch_user_schedule(user_id)