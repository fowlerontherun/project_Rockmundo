from auth.dependencies import get_current_user_id, require_role
# File: backend/routes/music_metrics_routes.py
from fastapi import APIRouter, Depends
from typing import Optional
from services.music_metrics import MusicMetricsService

router = APIRouter(prefix="/music/metrics", tags=["Music Metrics"])
svc = MusicMetricsService()

@router.get("/totals")
def get_totals(album_id: Optional[int] = None, song_id: Optional[int] = None):
    return svc.totals(album_id=album_id, song_id=song_id)
