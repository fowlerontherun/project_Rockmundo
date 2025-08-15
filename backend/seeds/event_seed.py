# seeds/event_seed.py

def get_seed_events():
    return [
        {"name": "Sprained Wrist", "type": "injury", "effect_type": "block_skill", "skill_affected": "guitar", "duration_days": 5, "trigger_chance": 0.01},
        {"name": "Lost Love for Guitar", "type": "burnout", "effect_type": "freeze_progress", "skill_affected": "guitar", "duration_days": 3, "trigger_chance": 0.01},
        {"name": "Throat Infection", "type": "illness", "effect_type": "block_skill", "skill_affected": "vocals", "duration_days": 4, "trigger_chance": 0.01},
        {"name": "Emotional Slump", "type": "emotional", "effect_type": "decay_skill", "skill_affected": "songwriting", "duration_days": 2, "trigger_chance": 0.01}
    ]
