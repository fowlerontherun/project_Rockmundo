from __future__ import annotations

import uuid
from typing import List, Optional

from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from services.media_event_service import media_event_service
from services.media_moderation_service import media_moderation_service
from services.media_service import (
    list_collaborations,
    request_collaboration,
    respond_to_collaboration,
)
from services.storage_service import get_storage_backend

router = APIRouter(prefix="/media")

# Simple in-memory store of uploaded media metadata.
_media_store: List[dict] = []


async def _current_user(user_id: int = Depends(get_current_user_id)) -> int:
    """Ensure the caller is an authenticated user."""

    await require_role(["user", "band_member", "moderator", "admin"], user_id)
    return user_id


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    song_id: Optional[int] = None,
    user_id: int = Depends(_current_user),
):
    """Upload a media file after moderation and store it via the storage backend.

    If ``song_id`` is provided, a publicity event is registered using the
    ``media_event_service`` to simulate the media helping the song trend.
    """

    data = await file.read()
    try:
        media_moderation_service.ensure_clean(data=data, filename=file.filename)
    except ValueError as exc:  # pragma: no cover - simple validation
        raise HTTPException(status_code=400, detail=str(exc))

    storage = get_storage_backend()
    key = f"media/{uuid.uuid4()}-{file.filename}"
    obj = storage.upload_bytes(data, key, content_type=file.content_type)

    if song_id is not None:
        media_event_service.tiktok_trend(song_id)

    item = {
        "id": len(_media_store) + 1,
        "owner_id": user_id,
        "filename": file.filename,
        "url": obj.url,
        "size": obj.size,
    }
    _media_store.append(item)
    return item


@router.get("/")
async def list_media() -> List[dict]:
    """List uploaded media items."""

    return _media_store


@router.post("/moderate")
async def moderate_media(
    file: UploadFile | None = File(default=None),
    text: Optional[str] = None,
):
    """Run moderation checks on the provided media or text."""

    data = await file.read() if file else None
    result = media_moderation_service.check(
        data=data, text=text, filename=file.filename if file else None
    )
    return {"allowed": result.allowed, "reasons": result.reasons}


@router.post("/collaborations")
async def create_collaboration(
    partner_id: int,
    details: Optional[str] = None,
    user_id: int = Depends(_current_user),
):
    """Initiate a collaboration request with another influencer."""

    return request_collaboration(user_id, partner_id, details)


@router.post("/collaborations/{collab_id}/respond")
async def respond_collaboration(
    collab_id: int,
    accept: bool,
    user_id: int = Depends(_current_user),
):
    """Accept or reject a collaboration request."""

    try:
        collab = respond_to_collaboration(collab_id, accept)
    except KeyError:  # pragma: no cover - simple guard
        raise HTTPException(status_code=404, detail="Collaboration not found")
    return collab


@router.get("/collaborations")
async def get_collaborations(user_id: int = Depends(_current_user)):
    """List collaborations involving the current user."""

    return list_collaborations(user_id)
