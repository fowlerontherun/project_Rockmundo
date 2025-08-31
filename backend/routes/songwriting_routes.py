"""Routes for AI-assisted songwriting features."""
from __future__ import annotations

from typing import Dict, Set, List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user_id
from backend.services.songwriting_service import songwriting_service

router = APIRouter(prefix="/songwriting", tags=["songwriting"])


class PromptPayload(BaseModel):
    prompt: str
    style: str


class DraftUpdate(BaseModel):
    lyrics: str | None = None
    chords: str | None = None
    themes: List[str] | None = None


@router.post("/prompt")
async def submit_prompt(payload: PromptPayload, user_id: int = Depends(get_current_user_id)):
    draft = await songwriting_service.generate_draft(user_id, payload.prompt, payload.style)
    return draft


@router.get("/drafts/{draft_id}")
def get_draft(draft_id: int, user_id: int = Depends(get_current_user_id)):
    draft = songwriting_service.get_draft(draft_id)
    if not draft or draft.creator_id != user_id:
        raise HTTPException(status_code=404, detail="draft_not_found")
    return draft


@router.put("/drafts/{draft_id}")
def edit_draft(draft_id: int, updates: DraftUpdate, user_id: int = Depends(get_current_user_id)):
    draft = songwriting_service.update_draft(
        draft_id,
        user_id,
        lyrics=updates.lyrics,
        chords=updates.chords,
        themes=updates.themes,
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
