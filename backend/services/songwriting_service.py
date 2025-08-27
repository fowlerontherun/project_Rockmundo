"""Service for AI-assisted songwriting generation and storage."""
from __future__ import annotations

from typing import Dict, List, Optional

from typing import Protocol, List

from backend.models.song import Song
from backend.models.songwriting import LyricDraft


class _Message:
    """Lightweight message object passed to the LLM."""

    def __init__(self, role: str, content: str) -> None:
        self.role = role
        self.content = content


class LLMProvider(Protocol):
    async def complete(self, history: List[_Message]) -> str: ...


class EchoLLM:
    async def complete(self, history: List[_Message]) -> str:  # pragma: no cover - trivial
        if history:
            return f"Echo: {history[-1].content}"
        return "..."


class SongwritingService:
    """Generate lyric drafts using an LLM and manage them."""

    def __init__(self, llm_client: Optional[LLMProvider] = None) -> None:
        self.llm = llm_client or EchoLLM()
        self._drafts: Dict[int, LyricDraft] = {}
        self._songs: Dict[int, Song] = {}
        self._counter = 1

    async def generate_draft(self, creator_id: int, prompt: str, style: str) -> LyricDraft:
        """Generate lyrics and chord suggestions for a prompt."""
        lyric_prompt = f"Write song lyrics in {style} style about: {prompt}"
        lyrics = await self.llm.complete([_Message(role="user", content=lyric_prompt)])
        chord_prompt = f"Suggest a chord progression for the following lyrics: {lyrics}"
        chords = await self.llm.complete([_Message(role="user", content=chord_prompt)])

        draft = LyricDraft(
            id=self._counter,
            creator_id=creator_id,
            prompt=prompt,
            style=style,
            lyrics=lyrics,
            chords=chords,
        )
        self._drafts[draft.id] = draft
        song = Song(
            id=draft.id,
            title=prompt[:30],
            duration_sec=0,
            genre=style,
            lyrics=lyrics,
            owner_band_id=creator_id,
        )
        self._songs[draft.id] = song
        self._counter += 1
        return draft

    def get_draft(self, draft_id: int) -> Optional[LyricDraft]:
        return self._drafts.get(draft_id)

    def list_drafts(self, creator_id: int) -> List[LyricDraft]:
        return [d for d in self._drafts.values() if d.creator_id == creator_id]

    def update_draft(
        self, draft_id: int, user_id: int, *, lyrics: Optional[str] = None, chords: Optional[str] = None
    ) -> LyricDraft:
        draft = self._drafts.get(draft_id)
        if not draft:
            raise KeyError("draft_not_found")
        if draft.creator_id != user_id:
            raise PermissionError("forbidden")
        if lyrics is not None:
            draft.lyrics = lyrics
            self._songs[draft_id].lyrics = lyrics
        if chords is not None:
            draft.chords = chords
        return draft

    def get_song(self, draft_id: int) -> Optional[Song]:
        return self._songs.get(draft_id)


songwriting_service = SongwritingService()
