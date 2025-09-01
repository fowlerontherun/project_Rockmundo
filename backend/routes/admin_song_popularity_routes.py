from typing import Optional

from auth.dependencies import require_role
from fastapi import APIRouter, Depends
from services.media_event_service import media_event_service
from services.media_monitor_service import media_monitor_service
from services.song_popularity_service import song_popularity_service

from pydantic import BaseModel

router = APIRouter(prefix="/song-popularity", tags=["Song Popularity"])


class MediaEvent(BaseModel):
    song_id: int
    boost: int = 10
    region_code: str = "global"
    platform: str = "any"


@router.post("/film", dependencies=[Depends(require_role(["admin"]))])
async def film(evt: MediaEvent):
    return media_event_service.film_placement(
        evt.song_id, evt.boost, evt.region_code, evt.platform
    )


@router.post("/tv", dependencies=[Depends(require_role(["admin"]))])
async def tv(evt: MediaEvent):
    return media_event_service.tv_placement(
        evt.song_id, evt.boost, evt.region_code, evt.platform
    )


@router.post("/tiktok", dependencies=[Depends(require_role(["admin"]))])
async def tiktok(evt: MediaEvent):
    return media_event_service.tiktok_trend(
        evt.song_id, evt.boost, evt.region_code, evt.platform
    )


@router.get("/events", dependencies=[Depends(require_role(["admin"]))])
async def list_events(song_id: Optional[int] = None, source: Optional[str] = None):
    return {"events": song_popularity_service.list_events(song_id, source=source)}


class MediaAdjust(BaseModel):
    song_id: int
    amount: int
    details: str = ""


@router.post("/media/poll", dependencies=[Depends(require_role(["admin"]))])
async def poll_media():
    return {"mentions": media_monitor_service.poll_feed()}


@router.post("/media/adjust", dependencies=[Depends(require_role(["admin"]))])
async def media_adjust(evt: MediaAdjust):
    return media_monitor_service.manual_adjust(evt.song_id, evt.amount, evt.details)
