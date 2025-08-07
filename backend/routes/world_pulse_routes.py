from fastapi import APIRouter
from models.world_pulse_models import *
from schemas.world_pulse_schemas import *

router = APIRouter()

@router.get("/worldpulse/trending_genres")
def trending_genres():
    return {"genres": ["Pop", "Punk", "EDM", "Rock"]}

@router.get("/worldpulse/karma_heatmap")
def karma_heatmap():
    return {"heatmap": {"London": 70, "Berlin": 45, "NYC": -20}}

@router.get("/worldpulse/event_stream")
def event_stream():
    return {"events": [
        "Band X released a new album.",
        "Band Y just won 'Best Live Act'.",
        "Band Z headlined MegaFest."
    ]}

@router.get("/worldpulse/top_influencers")
def top_influencers():
    return {"influencers": [
        {"band": "Neon Dreams", "score": 98},
        {"band": "Static Echo", "score": 93}
    ]}