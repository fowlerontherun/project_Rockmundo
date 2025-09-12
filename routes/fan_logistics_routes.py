from backend.auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Depends
from core.fan_logistics_engine import cast_vote, get_votes_for_band, get_top_petitions, trigger_engagement_bonus

router = APIRouter()

@router.post("/fan/vote")
def vote(band_id: int, city: str, fan_id: int):
    return cast_vote(band_id, city, fan_id)

@router.get("/fan/votes/{band_id}")
def votes(band_id: int):
    return get_votes_for_band(band_id)

@router.get("/fan/eligible_cities/{band_id}")
def petitions(band_id: int):
    return get_top_petitions(band_id)

@router.post("/fan/trigger_bonus")
def trigger_bonus(band_id: int, city: str):
    return trigger_engagement_bonus(band_id, city)