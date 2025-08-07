from fastapi import APIRouter
from services.scheduler_service import *

router = APIRouter()

@router.post("/notify/send")
def send_notification(payload: dict):
    return send_user_notification(payload)

@router.post("/scheduler/schedule_event")
def schedule_event(payload: dict):
    return schedule_game_event(payload)

@router.get("/scheduler/upcoming/{user_id}")
def get_upcoming_events(user_id: int):
    return fetch_user_schedule(user_id)