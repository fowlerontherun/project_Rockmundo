# routes/event_routes.py

from seeds.skill_seed import SKILL_NAME_TO_ID
from backend.services.event_service import apply_event_effect, roll_for_daily_event

from fastapi import APIRouter

router = APIRouter()

@router.post("/events/daily-roll")
def trigger_daily_event(user_id: int):
    lifestyle = {"drinking": "high"}  # normally from DB
    skills = [SKILL_NAME_TO_ID["vocals"], SKILL_NAME_TO_ID["guitar"]]
    event = roll_for_daily_event(user_id, lifestyle, skills)
    if event:
        apply_event_effect(user_id, event)
        return {"message": "Event triggered", "event": event}
    return {"message": "No event today"}
