"""Route definitions for random daily events."""

from fastapi import APIRouter

from seeds.skill_seed import SKILL_NAME_TO_ID
from services.event_service import apply_event_effect, roll_for_daily_event

from backend.schemas.events_schemas import EventRollRequest, EventRollResponse


router = APIRouter()


@router.post("/events/daily-roll", response_model=EventRollResponse)
def trigger_daily_event(payload: EventRollRequest) -> EventRollResponse:
    """Trigger a daily random event for a user and apply its effects."""

    lifestyle = {"drinking": "high"}  # normally from DB
    skills = [SKILL_NAME_TO_ID["vocals"], SKILL_NAME_TO_ID["guitar"]]
    event = roll_for_daily_event(payload.user_id, lifestyle, skills)
    if event:
        apply_event_effect(payload.user_id, event)
        return EventRollResponse(message="Event triggered", event=event)
    return EventRollResponse(message="No event today")
