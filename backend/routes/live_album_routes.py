from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.live_album_service import LiveAlbumService

router = APIRouter()
service = LiveAlbumService()


class CompileRequest(BaseModel):
    show_ids: List[int]
    album_title: str = "Live Compilation"


class TrackUpdateRequest(BaseModel):
    track_ids: List[int]


@router.post("/live_albums/compile")
def compile_live_album(payload: CompileRequest):
    try:
        return service.compile_live_album(payload.show_ids, payload.album_title)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/live_albums/{album_id}/tracks")
def update_live_album_tracks(album_id: int, payload: TrackUpdateRequest):
    try:
        return service.update_tracks(album_id, payload.track_ids)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/live_albums/{album_id}/publish")
def publish_live_album(album_id: int):
    try:
        new_id = service.publish_album(album_id)
        return {"album_id": new_id}
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=404, detail=str(exc))
