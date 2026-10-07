"""FastAPI catalogue routes for canonical songs."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth.dependencies import get_current_user_id
from services.band_service import BandService
from services.song_service import SongService

router = APIRouter(prefix="/songs", tags=["Songs"])
song_service = SongService()
band_service = BandService()


class SongCreatePayload(BaseModel):
    band_id: int = Field(..., gt=0)
    title: str
    duration_sec: int = Field(..., gt=0)
    genre: str
    lyrics: str = ""
    chord_progression: str = ""
    themes: list[str] = Field(default_factory=list)
    distribution_channels: list[str] = Field(default_factory=list)


def _require_band_member(band_id: int, user_id: int) -> dict:
    band = band_service.get_band_info(band_id)
    if not band:
        raise HTTPException(status_code=404, detail="band_not_found")
    members = {member.get("user_id") for member in band.get("members", [])}
    if user_id not in members:
        raise HTTPException(status_code=403, detail="band_membership_required")
    return band


@router.post("")
def create_song(
    payload: SongCreatePayload,
    user_id: int = Depends(get_current_user_id),
):
    _require_band_member(payload.band_id, user_id)
    result = song_service.create_song(
        {
            "band_id": payload.band_id,
            "title": payload.title.strip(),
            "duration_sec": payload.duration_sec,
            "genre": payload.genre.strip(),
            "royalties_split": {user_id: 100},
        }
    )
    return result


@router.get("/band/{band_id}")
def list_band_songs(
    band_id: int,
    search: Optional[str] = Query(default=None),
    sort: Optional[str] = Query(default=None),
    user_id: int = Depends(get_current_user_id),
):
    _require_band_member(band_id, user_id)
    return song_service.list_songs_by_band(band_id, search=search, sort=sort)


@router.get("/{song_id}")
def get_song(
    song_id: int,
    user_id: int = Depends(get_current_user_id),
):
    song = song_service.get_song(song_id)
    if not song:
        raise HTTPException(status_code=404, detail="song_not_found")
    _require_band_member(int(song["band_id"]), user_id)
    metadata = song_service.get_songwriting_metadata(song_id)
    if metadata:
        song["songwriting"] = metadata
    return song
