# File: backend/routes/music_metrics_routes.py
from typing import Optional

from backend.auth.dependencies import get_current_user_id, require_role  # noqa: F401
from backend.services.music_metrics import MusicMetricsService
from fastapi import APIRouter, Depends, HTTPException, Request  # noqa: F401

router = APIRouter(prefix="/music/metrics", tags=["Music Metrics"])
svc = MusicMetricsService()


@router.get("/totals")
def get_totals(album_id: Optional[int] = None, song_id: Optional[int] = None):
    return svc.totals(album_id=album_id, song_id=song_id)
