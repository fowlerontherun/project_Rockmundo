from datetime import datetime

replay_storage = {}

def log_player_event(data):
    user_id = data["user_id"]
    event = {
        "event_id": data["event_id"],
        "title": data["title"],
        "description": data["description"],
        "event_type": data["event_type"],
        "timestamp": str(datetime.utcnow()),
        "metadata": data.get("metadata", {})
    }
    if user_id not in replay_storage:
        replay_storage[user_id] = []
    replay_storage[user_id].append(event)
    return {"status": "logged", "event": event}

def get_player_replay_history(user_id):
    return {"replay_history": replay_storage.get(user_id, [])}

def get_replay_detail(user_id, event_id):
    user_events = replay_storage.get(user_id, [])
    for e in user_events:
        if e["event_id"] == event_id:
            return {"event": e}
    return {"error": "event not found"}