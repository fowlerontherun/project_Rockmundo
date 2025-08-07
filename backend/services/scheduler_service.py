from datetime import datetime, timedelta
import random

scheduled_events = []
user_notifications = []

def send_user_notification(payload):
    user_notifications.append(payload)
    return {"status": "sent", "payload": payload}

def schedule_game_event(payload):
    scheduled_events.append(payload)
    return {"status": "scheduled", "event": payload}

def fetch_user_schedule(user_id):
    return [e for e in scheduled_events if e["user_id"] == user_id]