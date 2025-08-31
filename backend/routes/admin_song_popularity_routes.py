from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth.dependencies import require_role
from services.media_event_service import media_event_service
from services.song_popularity_service import song_popularity_service

router = APIRouter(prefix="/song-popularity", tags=["Song Popularity"])


class MediaEvent(BaseModel):
    song_id: int
    boost: int = 10


@router.post("/film", dependencies=[Depends(require_role(["admin"]))])
async def film(evt: MediaEvent):
    return media_event_service.film_placement(evt.song_id, evt.boost)


@router.post("/tv", dependencies=[Depends(require_role(["admin"]))])
async def tv(evt: MediaEvent):
    return media_event_service.tv_placement(evt.song_id, evt.boost)


@router.post("/tiktok", dependencies=[Depends(require_role(["admin"]))])
async def tiktok(evt: MediaEvent):
    return media_event_service.tiktok_trend(evt.song_id, evt.boost)


@router.get("/events", dependencies=[Depends(require_role(["admin"]))])
async def list_events(song_id: Optional[int] = None):
    return {"events": song_popularity_service.list_events(song_id)}
