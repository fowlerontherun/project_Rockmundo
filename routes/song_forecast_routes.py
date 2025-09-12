from fastapi import APIRouter
from services.song_popularity_forecast import forecast_service

router = APIRouter(prefix="/songs", tags=["Song Forecast"])


@router.get("/{song_id}/forecast")
def get_song_forecast(song_id: int):
    """Return forecasted popularity for a song."""
    data = forecast_service.get_forecast(song_id)
    if not data:
        data = forecast_service.forecast_song(song_id)
    return {"song_id": song_id, "forecast": data}
