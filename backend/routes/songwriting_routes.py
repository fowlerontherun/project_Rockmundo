"""Routes for AI-assisted songwriting features."""
from __future__ import annotations

from typing import Dict, Set

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, validator

from backend.auth.dependencies import get_current_user_id
from backend.models.theme import THEMES
from backend.services.skill_service import skill_service
from backend.services.songwriting_service import songwriting_service

router = APIRouter(prefix="/songwriting", tags=["songwriting"])


class PromptPayload(BaseModel):
    title: str
    genre: str
    themes: list[str]

    @validator("themes")
    def validate_themes(cls, v: list[str]) -> list[str]:
        if len(v) != 3:
            raise ValueError("exactly_three_themes_required")
        for t in v:
            if t not in THEMES:
                raise ValueError("unknown_theme")
        return v


class DraftUpdate(BaseModel):
    lyrics: str | None = None
    themes: list[str] | None = None
    chord_progression: str | None = None
    album_art_url: str | None = None

    @validator("themes")
    def validate_themes(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        if len(v) != 3:
            raise ValueError("exactly_three_themes_required")
        for t in v:
            if t not in THEMES:
                raise ValueError("unknown_theme")
        return v


class CoWriterPayload(BaseModel):
    co_writer_id: int


@router.post("/prompt")
async def submit_prompt(payload: PromptPayload, user_id: int = Depends(get_current_user_id)):
    draft = await songwriting_service.generate_draft(
        creator_id=user_id,
        title=payload.title,
        genre=payload.genre,
        themes=payload.themes,
    )
    return draft


@router.get("/drafts")
def list_drafts(user_id: int = Depends(get_current_user_id)):
    return songwriting_service.list_drafts(user_id)


@router.get("/drafts/{draft_id}")
def get_draft(draft_id: int, user_id: int = Depends(get_current_user_id)):
    draft = songwriting_service.get_draft(draft_id)
    if not draft or draft.creator_id != user_id:
        raise HTTPException(status_code=404, detail="draft_not_found")
    return draft


@router.put("/drafts/{draft_id}")
def edit_draft(draft_id: int, updates: DraftUpdate, user_id: int = Depends(get_current_user_id)):
    draft = songwriting_service.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="draft_not_found")
    if draft.creator_id != user_id and user_id not in songwriting_service.get_co_writers(draft_id):
        raise HTTPException(status_code=403, detail="forbidden")
    draft = songwriting_service.update_draft(
        draft_id,
        user_id,
        lyrics=updates.lyrics,
        themes=updates.themes,
        chord_progression=updates.chord_progression,
        album_art_url=updates.album_art_url,

    )
    return draft



@router.get("/drafts/{draft_id}/versions")
def list_versions(draft_id: int, user_id: int = Depends(get_current_user_id)):
    draft = songwriting_service.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="draft_not_found")
    if draft.creator_id != user_id and user_id not in songwriting_service.get_co_writers(draft_id):
        raise HTTPException(status_code=403, detail="forbidden")
    return songwriting_service.list_versions(draft_id)


@router.get("/drafts/{draft_id}/co_writers")
def get_co_writers(draft_id: int, user_id: int = Depends(get_current_user_id)):
    draft = songwriting_service.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="draft_not_found")
    if draft.creator_id != user_id and user_id not in songwriting_service.get_co_writers(draft_id):
        raise HTTPException(status_code=403, detail="forbidden")
    return {"co_writers": list(songwriting_service.get_co_writers(draft_id))}


@router.post("/drafts/{draft_id}/co_writers")
def add_co_writer(
    draft_id: int,
    payload: CoWriterPayload,
    user_id: int = Depends(get_current_user_id),
):
    try:
        songwriting_service.add_co_writer(draft_id, user_id, payload.co_writer_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="draft_not_found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="forbidden")
    except ValueError as exc:
        if str(exc) == "cannot_invite_self":
            raise HTTPException(status_code=400, detail=str(exc))
        if str(exc) == "already_invited":
            raise HTTPException(status_code=409, detail=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))
    return {"co_writers": list(songwriting_service.get_co_writers(draft_id))}
@router.get("/themes")
def list_themes():
    return THEMES


@router.get("/skill")
def get_skill(user_id: int = Depends(get_current_user_id)):
    skill = skill_service.get_songwriting_skill(user_id)
    return {"xp": skill.xp, "level": skill.level}


# --- WebSocket for collaborative editing --------------------------------------
_subscribers: Dict[int, Set[WebSocket]] = {}


@router.websocket("/ws/{draft_id}")
async def songwriting_ws(ws: WebSocket, draft_id: int) -> None:
    await ws.accept()
    subs = _subscribers.setdefault(draft_id, set())
    subs.add(ws)
    try:
        while True:
            msg = await ws.receive_text()
            for peer in list(subs):
                if peer is not ws:
                    await peer.send_text(msg)
    except WebSocketDisconnect:  # pragma: no cover - network event
        subs.discard(ws)
        if not subs:
            _subscribers.pop(draft_id, None)
