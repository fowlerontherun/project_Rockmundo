"""Routes for managing seasonal events."""

from fastapi import APIRouter, Depends

from auth.dependencies import require_role
from services.events_service import (
    create_seasonal_event,
    end_seasonal_event,
    get_active_event,
    get_past_events,
)

from backend.schemas.events_schemas import (
    ActiveEventResponse,
    CreateEventSchema,
    EndEventSchema,
    EventHistoryResponse,
    EventResponse,
)


router = APIRouter()


@router.post(
    "/events/create",
    response_model=EventResponse,
    dependencies=[Depends(require_role(["user", "band_member", "moderator", "admin"]))],
)
def create_event(payload: CreateEventSchema) -> EventResponse:
    """Create and start a new seasonal event."""

    return create_seasonal_event(payload.model_dump())


@router.post("/events/end", response_model=EventResponse)
def end_event(payload: EndEventSchema) -> EventResponse:
    """End an existing seasonal event."""

    return end_seasonal_event(payload.event_id)


@router.get("/events/current", response_model=ActiveEventResponse)
def get_current_event() -> ActiveEventResponse:
    """Retrieve the currently active seasonal event."""

    return get_active_event()


@router.get("/events/history", response_model=EventHistoryResponse)
def get_event_history() -> EventHistoryResponse:
    """Return a list of past seasonal events."""

    return get_past_events()

