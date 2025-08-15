# seeds/lifestyle_seed.py

def get_default_lifestyle(user_id: int):
    return {
        "user_id": user_id,
        "sleep_hours": 7.0,
        "drinking": "none",
        "stress": 10.0,
        "training_discipline": 50.0,
        "mental_health": 100.0
    }
