"""Pydantic models for event-related operations.

This module defines request and response bodies used by the event
routers.  They provide type safety and power the generated OpenAPI
documentation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Event(BaseModel):
    """Representation of an in-game seasonal event."""

    event_id: str
    name: str
    theme: str
    description: str
    start_date: str
    end_date: Optional[str] = None
    modifiers: Dict[str, Any]
    active: bool = True


class CreateEventSchema(BaseModel):
    """Payload for creating a new seasonal event."""

    event_id: str
    name: str
    theme: str
    description: str
    start_date: str
    modifiers: Dict[str, Any]


class EndEventSchema(BaseModel):
    """Payload for ending an active seasonal event."""

    event_id: str


class ScheduleEventSchema(BaseModel):
    """Payload for scheduling a seasonal event."""

    event_id: str
    name: str
    theme: str
    description: str
    start_time: str
    end_time: str
    modifiers: Dict[str, Any]
    start_callback: Optional[str] = None
    end_callback: Optional[str] = None


class EventResponse(BaseModel):
    """Standard response after starting or ending an event."""

    status: str
    event: Event


class ActiveEventResponse(BaseModel):
    """Response model for retrieving the current active event."""

    active_event: Optional[Event]


class EventHistoryResponse(BaseModel):
    """Response model containing the history of past events."""

    history: List[Event]


class UpcomingEventsResponse(BaseModel):
    """Response model for upcoming scheduled events."""

    upcoming: List[Event]


class EventRollRequest(BaseModel):
    """Request body for rolling a daily random event."""

    user_id: int


class EventRollResponse(BaseModel):
    """Response after attempting to trigger a daily event."""

    message: str
    event: Optional[Dict[str, Any]] = None

