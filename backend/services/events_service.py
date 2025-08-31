from __future__ import annotations

from datetime import datetime
from threading import Timer
from typing import Any, Callable, Dict, List, Optional

# ---------------------------------------------------------------------------
# In-memory storage for events
# ---------------------------------------------------------------------------

# Completed and historical events
seasonal_events: List[Dict[str, Any]] = []
# The currently active event, if any
active_event: Optional[Dict[str, Any]] = None
# Events scheduled for the future mapped by ``event_id``
scheduled_events: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------------------------
# Callback registry
# ---------------------------------------------------------------------------


def apply_modifiers(event: Dict[str, Any]) -> None:
    """Dummy callback applying modifiers to game state.

    In a real implementation this would mutate global state. For the purposes
    of tests and demonstration we simply stash the modifiers on the event.
    """

    event.setdefault("applied_modifiers", event.get("modifiers", {}))


def remove_modifiers(event: Dict[str, Any]) -> None:
    """Reverse the effect of :func:`apply_modifiers`."""

    event.pop("applied_modifiers", None)


EVENT_CALLBACKS: Dict[str, Callable[[Dict[str, Any]], None]] = {
    "apply_modifiers": apply_modifiers,
    "remove_modifiers": remove_modifiers,
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _start_event(event_id: str) -> None:
    """Mark the event as active and invoke its start callback."""

    global active_event
    event = scheduled_events.get(event_id)
    if not event:
        return
    event["active"] = True
    event["start_date"] = datetime.utcnow().isoformat()
    active_event = event
    cb_name = event.get("start_callback")
    if cb_name:
        cb = EVENT_CALLBACKS.get(cb_name)
        if cb:
            cb(event)


def _end_event(event_id: str) -> None:
    """Deactivate the event and invoke its end callback."""

    global active_event
    event = scheduled_events.get(event_id)
    if not event:
        return
    event["active"] = False
    event["end_date"] = datetime.utcnow().isoformat()
    if active_event and active_event.get("event_id") == event_id:
        active_event = None
    cb_name = event.get("end_callback")
    if cb_name:
        cb = EVENT_CALLBACKS.get(cb_name)
        if cb:
            cb(event)
    seasonal_events.append(event)
    for t in event.get("timers", []):
        t.cancel()
    scheduled_events.pop(event_id, None)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def schedule_event(data: Dict[str, Any]) -> Dict[str, Any]:
    """Schedule a new event to automatically start and end.

    ``data`` must include ``event_id``, ``name``, ``theme``, ``description``,
    ``start_time`` and ``end_time`` in ISO format plus ``modifiers``. Optional
    ``start_callback`` and ``end_callback`` reference keys in
    :data:`EVENT_CALLBACKS`.
    """

    event_id = data["event_id"]
    start_time = datetime.fromisoformat(data["start_time"])
    end_time = datetime.fromisoformat(data["end_time"])

    event = {
        "event_id": event_id,
        "name": data["name"],
        "theme": data["theme"],
        "description": data["description"],
        "start_date": data["start_time"],
        "end_date": data["end_time"],
        "modifiers": data["modifiers"],
        "active": False,
        "start_callback": data.get("start_callback"),
        "end_callback": data.get("end_callback"),
        "timers": [],
    }

    now = datetime.utcnow()
    start_delay = max((start_time - now).total_seconds(), 0)
    end_delay = max((end_time - now).total_seconds(), 0)

    start_timer = Timer(start_delay, _start_event, args=[event_id])
    end_timer = Timer(end_delay, _end_event, args=[event_id])
    start_timer.start()
    end_timer.start()

    event["timers"] = [start_timer, end_timer]
    scheduled_events[event_id] = event
    return {"status": "scheduled", "event": event}


def cancel_scheduled_event(event_id: str) -> Dict[str, Any]:
    """Cancel a previously scheduled event."""

    event = scheduled_events.pop(event_id, None)
    if not event:
        return {"error": "event not found"}
    for t in event.get("timers", []):
        t.cancel()
    return {"status": "canceled", "event": event}


def get_upcoming_events() -> Dict[str, Any]:
    """Return a list of future events that have been scheduled."""

    return {"upcoming": list(scheduled_events.values())}


# ---------------------------------------------------------------------------
# Legacy helpers maintained for backwards compatibility
# ---------------------------------------------------------------------------


def create_seasonal_event(data: Dict[str, Any]) -> Dict[str, Any]:
    """Immediately create and activate a seasonal event."""

    global active_event
    event = {
        "event_id": data["event_id"],
        "name": data["name"],
        "theme": data["theme"],
        "description": data["description"],
        "start_date": data["start_date"],
        "end_date": None,
        "modifiers": data["modifiers"],
        "active": True,
    }
    seasonal_events.append(event)
    active_event = event
    return {"status": "event_started", "event": event}


def end_seasonal_event(event_id: str) -> Dict[str, Any]:
    """End an active seasonal event immediately."""

    global active_event
    for e in seasonal_events:
        if e["event_id"] == event_id:
            e["active"] = False
            e["end_date"] = datetime.utcnow().isoformat()
            if active_event and active_event["event_id"] == event_id:
                active_event = None
            return {"status": "event_ended", "event": e}
    return {"error": "event not found"}


def get_active_event() -> Dict[str, Any]:
    return {"active_event": active_event}


def get_past_events() -> Dict[str, Any]:
    return {"history": [e for e in seasonal_events if not e["active"]]}
