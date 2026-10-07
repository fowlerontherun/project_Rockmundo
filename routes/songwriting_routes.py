"""Routes for AI-assisted songwriting features."""
from __future__ import annotations

from typing import Dict, Set

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, validator

from auth.dependencies import get_current_user_id
from backend.models.theme import THEMES
from services.skill_service import skill_service
from services.songwriting_service import songwriting_service
from services.notifications_service import NotificationsService

router = APIRouter(prefix="/songwriting", tags=["songwriting"])
notifications = NotificationsService()


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
        if any(t not in THEMES for t in v):
            raise ValueError("unknown_theme")
        return v


class CoWriterPayload(BaseModel):
    co_writer_id: int


class LyricsPayload(BaseModel):
    themes: list[str]
    lines: int | None = 4

    @validator("themes")
    def validate_themes(cls, v: list[str]) -> list[str]:
        if len(v) != 3:
            raise ValueError("exactly_three_themes_required")
        for t in v:
            if t not in THEMES:
                raise ValueError("unknown_theme")
        return v


@router.post("/prompt")
async def submit_prompt(payload: PromptPayload, user_id: int = Depends(get_current_user_id)):
    draft = await songwriting_service.generate_draft(
        creator_id=user_id,
        title=payload.title,
        genre=payload.genre,
        themes=payload.themes,
    )
    return draft


@router.post("/lyrics")
def generate_lyrics(payload: LyricsPayload, user_id: int = Depends(get_current_user_id)):
    lyrics = songwriting_service.generate_lyrics(payload.themes, lines=payload.lines or 4)
    return {"lyrics": lyrics}


@router.get("/drafts")
def list_drafts(user_id: int = Depends(get_current_user_id)):
    return songwriting_service.list_drafts(user_id)


@router.get("/drafts/{draft_id}")
def get_draft(draft_id: int, user_id: int = Depends(get_current_user_id)):
    draft = songwriting_service.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="draft_not_found")
    if draft.creator_id != user_id and user_id not in songwriting_service.get_co_writers(draft_id):
        raise HTTPException(status_code=403, detail="forbidden")
    return draft


@router.put("/drafts/{draft_id}")
def edit_draft(draft_id: int, updates: DraftUpdate, user_id: int = Depends(get_current_user_id)):
    draft = songwriting_service.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="draft_not_found")
    if draft.creator_id != user_id and user_id not in songwriting_service.get_co_writers(draft_id):
        raise HTTPException(status_code=403, detail="forbidden")
    try:
        draft = songwriting_service.update_draft(
            draft_id,
            user_id,
            lyrics=updates.lyrics,
            themes=updates.themes,
            chord_progression=updates.chord_progression,
            album_art_url=updates.album_art_url,
        )
    except ValueError as exc:
        if str(exc) == "song_already_completed":
            raise HTTPException(status_code=409, detail=str(exc))
        raise
    return draft



def _format_minutes(total: int) -> str:
    hours, minutes = divmod(total, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _completion_body(summary: dict) -> str:
    time = summary["writing_time"]
    polish = summary["polish"]
    parts = [
        f"Writing time: {_format_minutes(time['total_minutes'])}",
        f"initial {_format_minutes(time['initial_minutes'])}",
        f"{time['revision_sessions']} revision session(s) / {_format_minutes(time['revision_minutes'])}",
    ]
    if time["polish_minutes"]:
        parts.append(f"polish {_format_minutes(time['polish_minutes'])}")
    body = f"{summary['title']} is complete. " + "; ".join(parts) + f". Song quality: {summary['quality_score']}/100."
    if polish["available"]:
        body += f" You can do one final polish session with a {polish['success_chance']}% chance of improving it."
    return body


def _notify_songwriters(draft_id: int, title: str, body: str, type_: str) -> None:
    draft = songwriting_service.get_draft(draft_id)
    if not draft:
        return
    recipients = {draft.creator_id, *songwriting_service.get_co_writers(draft_id)}
    for recipient in recipients:
        try:
            notifications.create(
                user_id=recipient,
                title=title,
                body=body,
                type_=type_,
            )
        except Exception:
            # Completion state should never be rolled back by an inbox outage.
            pass


@router.post("/drafts/{draft_id}/complete")
def complete_songwriting(
    draft_id: int,
    user_id: int = Depends(get_current_user_id),
):
    try:
        summary = songwriting_service.complete_song(draft_id, user_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="draft_not_found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="forbidden")

    if summary["newly_completed"]:
        _notify_songwriters(
            draft_id,
            title=f"Song complete: {summary['title']}",
            body=_completion_body(summary),
            type_="songwriting_complete",
        )
    return summary


@router.post("/drafts/{draft_id}/polish")
def polish_songwriting(
    draft_id: int,
    user_id: int = Depends(get_current_user_id),
):
    try:
        summary = songwriting_service.polish_song(draft_id, user_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="draft_not_found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="forbidden")
    except ValueError as exc:
        detail = str(exc)
        if detail in {"song_not_completed", "polish_already_attempted", "polish_already_resolved"}:
            raise HTTPException(status_code=409, detail=detail)
        raise

    polish = summary["polish"]
    if polish["succeeded"]:
        title = f"Polish worked: {summary['title']}"
        result = f"The extra session added {polish['quality_bonus']} quality points."
    else:
        title = f"Polish finished: {summary['title']}"
        result = "The extra session did not improve the song this time."
    _notify_songwriters(
        draft_id,
        title=title,
        body=f"{result} Final song quality: {summary['quality_score']}/100. Total writing time: {_format_minutes(summary['writing_time']['total_minutes'])}.",
        type_="songwriting_polish",
    )
    return summary


@router.post("/drafts/{draft_id}/skip-polish")
def skip_songwriting_polish(
    draft_id: int,
    user_id: int = Depends(get_current_user_id),
):
    try:
        return songwriting_service.skip_polish(draft_id, user_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="draft_not_found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="forbidden")
    except ValueError as exc:
        detail = str(exc)
        if detail in {"song_not_completed", "polish_already_resolved"}:
            raise HTTPException(status_code=409, detail=detail)
        raise


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
        songwriting_service.invite_co_writer(draft_id, user_id, payload.co_writer_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="draft_not_found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="forbidden")
    except ValueError as exc:
        if str(exc) == "cannot_invite_self":
            raise HTTPException(status_code=400, detail=str(exc))
        if str(exc) in {"already_invited", "already_collaborating"}:
            raise HTTPException(status_code=409, detail=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))

    draft = songwriting_service.get_draft(draft_id)
    try:
        notifications.create(
            user_id=payload.co_writer_id,
            title="Songwriting session invitation",
            body=f"You have been invited to co-write '{draft.title}'. Open Songwriting to accept or decline.",
            type_="songwriting_invite",
        )
    except Exception:
        # The invite itself remains valid even if realtime/notification delivery
        # is temporarily unavailable; it will still appear in pending invites.
        pass

    return {
        "co_writers": list(songwriting_service.get_co_writers(draft_id)),
        "pending_invitees": list(songwriting_service.get_pending_invitees(draft_id)),
    }
@router.get("/invites")
def list_songwriting_invites(user_id: int = Depends(get_current_user_id)):
    return {"invites": songwriting_service.list_pending_invites(user_id)}


@router.post("/invites/{draft_id}/accept")
def accept_songwriting_invite(
    draft_id: int,
    user_id: int = Depends(get_current_user_id),
):
    try:
        songwriting_service.accept_co_writer_invite(draft_id, user_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="invite_not_found")

    draft = songwriting_service.get_draft(draft_id)
    if draft:
        try:
            notifications.create(
                user_id=draft.creator_id,
                title="Songwriting invitation accepted",
                body=f"A player accepted the invitation to co-write '{draft.title}'.",
                type_="songwriting_invite",
            )
        except Exception:
            pass
    return {"ok": True, "draft_id": draft_id}


@router.post("/invites/{draft_id}/decline")
def decline_songwriting_invite(
    draft_id: int,
    user_id: int = Depends(get_current_user_id),
):
    try:
        songwriting_service.decline_co_writer_invite(draft_id, user_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="invite_not_found")
    return {"ok": True, "draft_id": draft_id}


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
async def songwriting_ws(
    ws: WebSocket,
    draft_id: int,
    user_id: int = Depends(get_current_user_id),
) -> None:
    draft = songwriting_service.get_draft(draft_id)
    if not draft or (
        draft.creator_id != user_id
        and user_id not in songwriting_service.get_co_writers(draft_id)
    ):
        await ws.close(code=1008)
        return
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
