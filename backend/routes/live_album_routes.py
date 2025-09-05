from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.live_album_service import LiveAlbumService

router = APIRouter()
service = LiveAlbumService()


class CompileRequest(BaseModel):
    show_ids: List[int]
    album_title: str = "Live Compilation"


@router.post("/live_albums/compile")
def compile_live_album(payload: CompileRequest):
    try:
        return service.compile_live_album(payload.show_ids, payload.album_title)
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=str(exc))
