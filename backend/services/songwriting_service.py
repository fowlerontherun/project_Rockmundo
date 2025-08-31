"""Service for AI-assisted songwriting generation and storage."""
from __future__ import annotations

from typing import Dict, List, Optional, Set

from typing import Protocol

from backend.models.song import Song

from backend.models.songwriting import GenerationMetadata, LyricDraft
from backend.models.songwriting import LyricDraft
from backend.models.song_draft_version import SongDraftVersion
from backend.services.ai_art_service import AIArtService, ai_art_service
from backend.services.skill_service import SkillService, skill_service as skill_service_instance


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
        skill_service: SkillService | None = None,
    ) -> None:
        self.llm = llm_client or EchoLLM()
        self.art_service = art_service or ai_art_service
        self.skill_service = skill_service or skill_service_instance
        self._drafts: Dict[int, LyricDraft] = {}
        self._songs: Dict[int, Song] = {}
        self._co_writers: Dict[int, Set[int]] = {}
        self._versions: Dict[int, List[SongDraftVersion]] = {}
        self._counter = 1

    async def generate_draft(
        self, creator_id: int, title: str, genre: str, themes: List[str]
    ) -> LyricDraft:
        """Generate lyrics, chords and album art for a song idea."""

        if len(themes) != 3:
            raise ValueError("exactly_three_themes_required")

        theme_str = ", ".join(themes)
        skill = self.skill_service.get_songwriting_skill(creator_id)
        quality_mod = 1.0 + 0.1 * (skill.level - 1)
        lyric_prompt = (
            f"Write {genre} song lyrics titled '{title}' focusing on themes: {theme_str}."
            f" Aim for quality modifier {quality_mod:.1f}."
        )
        lyrics = await self.llm.complete([_Message(role="user", content=lyric_prompt)])

        chord_prompt = (
            f"Suggest a chord progression for a {genre} song titled '{title}' about {theme_str}."
            f" Quality modifier {quality_mod:.1f}."
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
            metadata=GenerationMetadata(quality_modifier=quality_mod),
        )
        self._drafts[draft.id] = draft
        song = Song(
            id=draft.id,
            title=title,
            duration_sec=0,
            genre_id=0,
            genre_id=None,

            lyrics=lyrics,
            themes=themes,
            chord_progression=chord_progression,
            album_art_url=art_url,
            owner_band_id=creator_id,
        )
        self._songs[draft.id] = song
        # record initial version
        self.save_version(draft.id, creator_id, lyrics, chords)
        self._counter += 1
        self.skill_service.add_songwriting_xp(creator_id)
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
        chords: Optional[str] = None,
        themes: Optional[List[str]] = None,

        chord_progression: Optional[str] = None,
        album_art_url: Optional[str] = None,

    ) -> LyricDraft:
        draft = self._drafts.get(draft_id)
        if not draft:
            raise KeyError("draft_not_found")
        if draft.creator_id != user_id and user_id not in self._co_writers.get(draft_id, set()):
            raise PermissionError("forbidden")
        if lyrics is not None:
            draft.lyrics = lyrics
            self._songs[draft_id].lyrics = lyrics

        if chords is not None:
            draft.chords = chords
        # save snapshot of current state
        self.save_version(draft_id, user_id, draft.lyrics, draft.chords, themes)

        if chord_progression is not None:
            draft.chord_progression = chord_progression
            self._songs[draft_id].chord_progression = chord_progression
        if album_art_url is not None:
            draft.album_art_url = album_art_url
            self._songs[draft_id].album_art_url = album_art_url
        self.skill_service.add_songwriting_xp(user_id, revised=True)

        return draft

    def add_co_writer(self, draft_id: int, user_id: int, co_writer_id: int) -> None:
        draft = self._drafts.get(draft_id)
        if not draft:
            raise KeyError("draft_not_found")
        if draft.creator_id != user_id and user_id not in self._co_writers.get(draft_id, set()):
            raise PermissionError("forbidden")
        self._co_writers.setdefault(draft_id, set()).add(co_writer_id)

    def save_version(
        self,
        draft_id: int,
        author_id: int,
        lyrics: str,
        chords: Optional[str] = None,
        themes: Optional[List[str]] = None,
    ) -> SongDraftVersion:
        version = SongDraftVersion(
            author_id=author_id,
            lyrics=lyrics,
            chords=chords,
            themes=themes or [],
        )
        self._versions.setdefault(draft_id, []).append(version)
        return version

    def list_versions(self, draft_id: int) -> List[SongDraftVersion]:
        return list(self._versions.get(draft_id, []))

    def get_co_writers(self, draft_id: int) -> Set[int]:
        return set(self._co_writers.get(draft_id, set()))

    def get_song(self, draft_id: int) -> Optional[Song]:
        return self._songs.get(draft_id)


songwriting_service = SongwritingService()
