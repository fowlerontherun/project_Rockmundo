"""Route definitions for event-related actions."""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from seeds.skill_seed import SKILL_NAME_TO_ID
from services.event_service import (
    apply_event_effect,
    list_workshops,
    purchase_workshop_ticket,
    roll_for_daily_event,
)

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


@router.get("/events/workshops")
def get_workshops():
    """List all upcoming workshops."""

    return {"workshops": [asdict(w) for w in list_workshops()]}


@router.post("/events/workshops/{event_id}/purchase")
def purchase_workshop(event_id: int, user_id: int):
    """Purchase a ticket for a workshop and register attendance."""

    try:
        workshop = purchase_workshop_ticket(user_id, event_id)
    except ValueError as exc:  # pragma: no cover - simple passthrough
        raise HTTPException(status_code=400, detail=str(exc))
    return {"workshop": asdict(workshop)}
