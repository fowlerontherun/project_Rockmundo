# services/event_service.py

from datetime import datetime, timedelta
import random

def roll_for_daily_event(user_id, lifestyle_data, active_skills):
    # Sample logic: if drinking high and vocals practiced 5 days in a row
    if lifestyle_data.get("drinking") == "high" and "vocals" in active_skills:
        if random.random() < 0.15:
            return {"event": "vocal fatigue", "effect": "freeze_progress", "skill": "vocals", "duration": 3}

    if random.random() < 0.01:
        return {"event": "sprained wrist", "effect": "block_skill", "skill": "guitar", "duration": 5}

    return None

def apply_event_effect(user_id, event_data):
    # Store in database as active event
    print(f"Applied {event_data} to user {user_id}")

def clear_expired_events():
    # Clear events whose start_date + duration_days < today
    pass

def is_skill_blocked(user_id, skill):
    # Check if user has an active event blocking this skill
    return False
