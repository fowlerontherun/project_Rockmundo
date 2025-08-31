"""Service for AI-assisted songwriting generation and storage."""
from __future__ import annotations

from typing import Dict, List, Optional

from typing import Protocol

from backend.models.song import Song
from backend.models.songwriting import LyricDraft
from backend.services.ai_art_service import AIArtService, ai_art_service


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

    def __init__(
        self,
        llm_client: Optional[LLMProvider] = None,
        art_service: Optional[AIArtService] = None,
    ) -> None:
        self.llm = llm_client or EchoLLM()
        self.art_service = art_service or ai_art_service
        self._drafts: Dict[int, LyricDraft] = {}
        self._songs: Dict[int, Song] = {}
        self._counter = 1

    async def generate_draft(
        self, creator_id: int, title: str, genre: str, themes: List[str]
    ) -> LyricDraft:
        """Generate lyrics, chords and album art for a song idea."""

        if len(themes) != 3:
            raise ValueError("exactly_three_themes_required")

        theme_str = ", ".join(themes)
        lyric_prompt = (
            f"Write {genre} song lyrics titled '{title}' focusing on themes: {theme_str}."
        )
        lyrics = await self.llm.complete([_Message(role="user", content=lyric_prompt)])

        chord_prompt = (
            f"Suggest a chord progression for a {genre} song titled '{title}' about {theme_str}."
        )
        chord_progression = await self.llm.complete([_Message(role="user", content=chord_prompt)])
        chord_progression = chord_progression.strip() or "C G Am F"

        try:
            art_url = await self.art_service.generate_album_art(title, themes)
        except Exception:
            art_url = None

        draft = LyricDraft(
            id=self._counter,
            creator_id=creator_id,
            title=title,
            genre=genre,
            themes=themes,
            lyrics=lyrics,
            chord_progression=chord_progression,
            album_art_url=art_url,
        )
        self._drafts[draft.id] = draft
        song = Song(
            id=draft.id,
            title=title,
            duration_sec=0,
            genre_id=None,
            lyrics=lyrics,
            themes=themes,
            chord_progression=chord_progression,
            album_art_url=art_url,
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
        self,
        draft_id: int,
        user_id: int,
        *,
        lyrics: Optional[str] = None,
        chord_progression: Optional[str] = None,
        album_art_url: Optional[str] = None,
    ) -> LyricDraft:
        draft = self._drafts.get(draft_id)
        if not draft:
            raise KeyError("draft_not_found")
        if draft.creator_id != user_id:
            raise PermissionError("forbidden")
        if lyrics is not None:
            draft.lyrics = lyrics
            self._songs[draft_id].lyrics = lyrics
        if chord_progression is not None:
            draft.chord_progression = chord_progression
            self._songs[draft_id].chord_progression = chord_progression
        if album_art_url is not None:
            draft.album_art_url = album_art_url
            self._songs[draft_id].album_art_url = album_art_url
        return draft

    def get_song(self, draft_id: int) -> Optional[Song]:
        return self._songs.get(draft_id)


songwriting_service = SongwritingService()
