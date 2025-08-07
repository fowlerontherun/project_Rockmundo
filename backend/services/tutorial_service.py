# Simulated storage
user_tutorials = {}
contextual_tips = {
    "character_creation": "Choose a style that reflects your future genre.",
    "first_gig": "Don’t forget to rehearse!",
    "album_release": "Promote before release for better sales.",
    "tour_planning": "Start small — fame spreads city by city."
}

def start_user_tutorial(user_id):
    user_tutorials[user_id] = {"steps": [], "completed": False}
    return {"status": "started", "user_id": user_id}

def mark_step_complete(user_id, step):
    if user_id not in user_tutorials:
        user_tutorials[user_id] = {"steps": [], "completed": False}
    user_tutorials[user_id]["steps"].append(step)
    return {"status": "step_complete", "user_id": user_id, "step": step}

def get_contextual_tip(stage):
    return {"tip": contextual_tips.get(stage, "No tip available.")}