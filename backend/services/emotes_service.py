import time

unlocked_emotes = {
    1: ["wave", "cheer", "headbang"],
    2: ["wave", "bow", "salute", "invite_fan"]
}

last_used_emote = {}

emote_definitions = {
    "wave": {"category": "standard", "cooldown": 5},
    "cheer": {"category": "standard", "cooldown": 5},
    "headbang": {"category": "standard", "cooldown": 10},
    "bow": {"category": "contextual", "cooldown": 15},
    "salute": {"category": "contextual", "cooldown": 10},
    "invite_fan": {"category": "stage", "cooldown": 30}
}

def trigger_player_emote(data):
    user_id = data["user_id"]
    emote_id = data["emote_id"]
    context = data["context"]

    if emote_id not in unlocked_emotes.get(user_id, []):
        return {"error": "emote not unlocked"}

    cooldown = emote_definitions.get(emote_id, {}).get("cooldown", 0)
    last_used = last_used_emote.get((user_id, emote_id), 0)
    now = time.time()

    if now - last_used < cooldown:
        return {"error": "emote on cooldown", "cooldown_remaining": cooldown - (now - last_used)}

    last_used_emote[(user_id, emote_id)] = now
    return {
        "status": "emote_triggered",
        "user_id": user_id,
        "emote_id": emote_id,
        "context": context
    }

def list_unlocked_emotes(user_id):
    return {
        "user_id": user_id,
        "emotes": unlocked_emotes.get(user_id, [])
    }