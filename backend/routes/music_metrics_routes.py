# File: backend/routes/music_metrics_routes.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request  # noqa: F401

from backend.auth.dependencies import get_current_user_id, require_role  # noqa: F401
from backend.services import song_popularity_service
from backend.services.song_popularity_forecast import forecast_service
from backend.services.music_metrics import MusicMetricsService

router = APIRouter(prefix="/music/metrics", tags=["Music Metrics"])
svc = MusicMetricsService()


@router.get("/totals")
def get_totals(album_id: Optional[int] = None, song_id: Optional[int] = None):
    return svc.totals(album_id=album_id, song_id=song_id)


@router.get("/songs/{song_id}/popularity")
def get_song_popularity(
    song_id: int,
    region_code: str = "global",
    platform: str = "any",
):
    """Return popularity analytics for a song."""
    return {
        "song_id": song_id,
        "current_popularity": song_popularity_service.get_current_popularity(
            song_id, region_code, platform
        ),
        "half_life_days": song_popularity_service.HALF_LIFE_DAYS,
        "last_boost_source": song_popularity_service.get_last_boost_source(
            song_id, region_code, platform
        ),
        "history": song_popularity_service.get_history(
            song_id, region_code, platform
        ),
        "breakdown": song_popularity_service.get_breakdown(song_id),
    }


@router.get("/songs/{song_id}/forecast")
def get_song_forecast(song_id: int):
    data = forecast_service.get_forecast(song_id)
    if not data:
        data = forecast_service.forecast_song(song_id)
    return {"song_id": song_id, "forecast": data}
