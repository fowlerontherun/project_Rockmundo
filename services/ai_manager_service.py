from backend.config import ENABLE_PR_AI_MANAGER, ENABLE_TOUR_AI_MANAGER


# Simulated planner engine
def activate_ai_manager(data):
    """Activate a generic AI manager persona."""
    return {
        "message": f"AI Manager for {data['type']} activated with persona {data['persona']}"
    }


def get_band_suggestions(band_id: int):
    """Return general management tips for a band."""
    suggestions = [
        {
            "suggestion_type": "tour",
            "content": "Book 3 shows in the UK this month",
            "impact_estimate": "High",
        },
        {
            "suggestion_type": "release",
            "content": "Drop a teaser on TikkaTok before the album launch",
            "impact_estimate": "Moderate",
        },
        {
            "suggestion_type": "media",
            "content": "Issue a statement addressing the festival incident",
            "impact_estimate": "Reputation boost",
        },
    ]
    return {"band_id": band_id, "suggestions": suggestions}


def override_ai_manager(data):
    """Accept a manual override for the manager."""
    return {"message": f"Override accepted: {data['action']}"}


# --- Extensions for tour / PR managers ------------------------------------

def activate_tour_manager(profile: dict) -> dict:
    """Activate the specialised tour manager AI if enabled."""
    if not ENABLE_TOUR_AI_MANAGER:
        return {"error": "Tour manager AI is disabled"}
    profile = dict(profile)
    profile["type"] = "tour"
    return activate_ai_manager(profile)


def activate_pr_manager(profile: dict) -> dict:
    """Activate the specialised PR manager AI if enabled."""
    if not ENABLE_PR_AI_MANAGER:
        return {"error": "PR manager AI is disabled"}
    profile = dict(profile)
    profile["type"] = "pr"
    return activate_ai_manager(profile)


def get_tour_suggestions(band_id: int) -> dict:
    """Provide tour planning tips from the AI tour manager."""
    if not ENABLE_TOUR_AI_MANAGER:
        return {"band_id": band_id, "suggestions": []}
    tips = [
        {
            "suggestion_type": "routing",
            "content": "Optimize route for lower travel costs",
            "impact_estimate": "Medium",
        },
        {
            "suggestion_type": "venue",
            "content": "Consider mid-sized venues in Germany",
            "impact_estimate": "High",
        },
    ]
    return {"band_id": band_id, "suggestions": tips}


def get_pr_suggestions(band_id: int) -> dict:
    """Provide publicity suggestions from the AI PR manager."""
    if not ENABLE_PR_AI_MANAGER:
        return {"band_id": band_id, "suggestions": []}
    tips = [
        {
            "suggestion_type": "press_release",
            "content": "Announce charity collaboration to gain positive press",
            "impact_estimate": "Positive",
        },
        {
            "suggestion_type": "social_media",
            "content": "Engage fans with a live Q&A session",
            "impact_estimate": "Moderate",
        },
    ]
    return {"band_id": band_id, "suggestions": tips}
