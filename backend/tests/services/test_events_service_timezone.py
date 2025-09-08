from datetime import datetime, timedelta

from backend.services import events_service


def test_schedule_event_stores_timezone(monkeypatch):
    start = datetime.utcnow() + timedelta(hours=1)
    end = start + timedelta(hours=2)
    data = {
        "event_id": "tz1",
        "name": "Test",
        "theme": "none",
        "description": "desc",
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "timezone": "UTC",
        "modifiers": {},
    }
    result = events_service.schedule_event(data)
    assert result["event"]["timezone"] == "UTC"
    events_service.cancel_scheduled_event("tz1")


def test_update_event_changes_times(monkeypatch):
    start = datetime.utcnow() + timedelta(hours=1)
    end = start + timedelta(hours=2)
    data = {
        "event_id": "tz2",
        "name": "Test",
        "theme": "none",
        "description": "desc",
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "timezone": "UTC",
        "modifiers": {},
    }
    events_service.schedule_event(data)
    new_start = start + timedelta(hours=2)
    new_end = end + timedelta(hours=2)
    update = events_service.update_scheduled_event(
        "tz2", new_start.isoformat(), new_end.isoformat(), "UTC"
    )
    assert update["event"]["start_date"].startswith(new_start.isoformat()[:19])
    events_service.cancel_scheduled_event("tz2")
