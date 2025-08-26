from auth.dependencies import get_current_user_id, require_role
# routes/event_routes.py

from fastapi import APIRouter, Depends
from services.event_service import roll_for_daily_event, apply_event_effect

router = APIRouter()

@router.post("/events/daily-roll")
def trigger_daily_event(user_id: int):
    lifestyle = {"drinking": "high"}  # normally from DB
    skills = ["vocals", "guitar"]
    event = roll_for_daily_event(user_id, lifestyle, skills)
    if event:
        apply_event_effect(user_id, event)
        return {"message": "Event triggered", "event": event}
    return {"message": "No event today"}
