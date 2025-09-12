from models.ai_tour_manager import AITourManagerSettings
from models.tour import Tour
from models.venue import Venue
from typing import List

# Dummy in-memory storage (replace with DB in real implementation)
tours: List[Tour] = []
venues: List[Venue] = []
ai_settings: List[AITourManagerSettings] = []
scheduled_tours: List[dict] = []

def auto_schedule_tour(settings: AITourManagerSettings):
    available_venues = [
        v for v in venues 
        if (not settings.preferred_countries or v.country in settings.preferred_countries)
    ]

    selected_venues = []
    total_cost = 0.0

    for venue in available_venues:
        if len(selected_venues) >= 5:
            break
        if settings.max_cost and (total_cost + venue.rental_cost > settings.max_cost):
            continue
        selected_venues.append(venue)
        total_cost += venue.rental_cost

    tour_plan = {
        "band_id": settings.band_id,
        "venues": [v.name for v in selected_venues],
        "estimated_cost": total_cost,
        "status": "scheduled"
    }

    scheduled_tours.append(tour_plan)
    return tour_plan

def run_ai_scheduler():
    results = []
    for setting in ai_settings:
        if setting.enabled:
            result = auto_schedule_tour(setting)
            results.append(result)
    return results