"""Admin routes for managing scheduled world events."""

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends

from backend.auth.dependencies import require_permission
from backend.schemas.events_schemas import (
    EndEventSchema,
    EventResponse,
    ScheduleEventSchema,
    UpdateEventSchema,
    UpcomingEventsResponse,
)
from backend.services.events_service import (
    cancel_scheduled_event,
    get_upcoming_events,
    schedule_event,
    update_scheduled_event,
)

router = APIRouter(prefix="/events", dependencies=[Depends(require_permission(["admin"]))])


def _to_utc_naive(ts: str, tz: str) -> str:
    """Convert an ISO timestamp to naive UTC based on provided timezone."""

    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    zone = ZoneInfo(tz)
    return dt.astimezone(zone).astimezone(ZoneInfo("UTC")).replace(tzinfo=None).isoformat()


@router.post("/schedule", response_model=EventResponse)
def schedule(payload: ScheduleEventSchema) -> EventResponse:
    start = _to_utc_naive(payload.start_time, payload.timezone)
    end = _to_utc_naive(payload.end_time, payload.timezone)
    data = payload.model_dump()
    data["start_time"] = start
    data["end_time"] = end
    return schedule_event(data)


@router.post("/update", response_model=EventResponse)
def update(payload: UpdateEventSchema) -> EventResponse:
    start = _to_utc_naive(payload.start_time_utc, payload.timezone)
    end = _to_utc_naive(payload.end_time_utc, payload.timezone)
    return update_scheduled_event(payload.event_id, start, end, payload.timezone)


@router.post("/cancel", response_model=EventResponse)
def cancel(payload: EndEventSchema) -> EventResponse:
    return cancel_scheduled_event(payload.event_id)


@router.get("/upcoming", response_model=UpcomingEventsResponse)
def upcoming() -> UpcomingEventsResponse:
    return get_upcoming_events()

