from datetime import datetime

seasonal_events = []
active_event = None

def create_seasonal_event(data):
    global active_event
    event = {
        "event_id": data["event_id"],
        "name": data["name"],
        "theme": data["theme"],
        "description": data["description"],
        "start_date": data["start_date"],
        "end_date": None,
        "modifiers": data["modifiers"],
        "active": True
    }
    seasonal_events.append(event)
    active_event = event
    return {"status": "event_started", "event": event}

def end_seasonal_event(event_id):
    global active_event
    for e in seasonal_events:
        if e["event_id"] == event_id:
            e["active"] = False
            e["end_date"] = str(datetime.utcnow())
            if active_event and active_event["event_id"] == event_id:
                active_event = None
            return {"status": "event_ended", "event": e}
    return {"error": "event not found"}

def get_active_event():
    return {"active_event": active_event}

def get_past_events():
    return {"history": [e for e in seasonal_events if not e["active"]]}