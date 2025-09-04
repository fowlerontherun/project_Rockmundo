"""Service for AI-assisted songwriting generation and storage."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Optional, Protocol, Set

from backend.models.song import Song
from backend.models.song_draft_version import SongDraftVersion
from backend.models.songwriting import GenerationMetadata, LyricDraft
from backend.services.ai_art_service import AIArtService, ai_art_service
from backend.services.chemistry_service import ChemistryService
from backend.services.originality_service import (
    OriginalityService,
    originality_service,
)
from backend.services.skill_service import (
    SkillService,
    skill_service as skill_service_instance,
)
from backend.services.band_service import BandService

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from backend.services.legal_service import LegalService


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
        originality: Optional[OriginalityService] = None,
        legal: Optional[LegalService] = None,
        skill_service: SkillService | None = None,
        band_service: BandService | None = None,
        chemistry_service: ChemistryService | None = None,
    ) -> None:
        self.llm = llm_client or EchoLLM()
        self.art_service = art_service or ai_art_service
        self.originality = originality or originality_service
        self.legal = legal
        self.skill_service = skill_service or skill_service_instance
        self.band_service = band_service
        self.chemistry_service = chemistry_service or ChemistryService()
        self._drafts: Dict[int, LyricDraft] = {}
        self._songs: Dict[int, Song] = {}
        self._co_writers: Dict[int, Set[int]] = {}
        self._versions: Dict[int, List[SongDraftVersion]] = {}
        self._counter = 1

    async def generate_draft(
        self,
        creator_id: int,
        title: str,
        genre: str,
        themes: List[str],
        *,
        register_copyright: bool = False,
    ) -> LyricDraft:
        """Generate lyrics, chord progression and album art for a song idea."""

        if len(themes) != 3:
            raise ValueError("exactly_three_themes_required")

        theme_str = ", ".join(themes)
        skill = self.skill_service.get_songwriting_skill(creator_id)

        participants = [creator_id] + list(self._co_writers.get(self._counter, set()))
        scores: list[float] = []
        for i, a in enumerate(participants):
            for b in participants[i + 1 :]:
                pair = self.chemistry_service.initialize_pair(a, b)
                scores.append(pair.score)
        avg_chem = sum(scores) / len(scores) if scores else 50.0
        chemistry_mod = (avg_chem - 50.0) / 100.0
        quality_mod = (1.0 + 0.1 * (skill.level - 1)) * (1 + chemistry_mod)
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

        record, duplicate = self.originality.register_lyrics(lyrics, self._counter)
        warning = "possible_plagiarism" if duplicate else None
        if duplicate and self.legal:
            # log dispute for record keeping
            self.legal.create_case(0, creator_id, f"duplicate_lyrics:{record.hash}")

        draft = LyricDraft(
            id=self._counter,
            creator_id=creator_id,
            title=title,
            genre=genre,
            themes=themes,
            lyrics=lyrics,
            chord_progression=chord_progression,
            album_art_url=art_url,
            plagiarism_warning=warning,
            metadata=GenerationMetadata(quality_modifier=quality_mod),
        )
        self._drafts[draft.id] = draft
        song = Song(
            draft.id,
            title,
            0,
            None,
            lyrics,
            creator_id,
            themes=themes,
            chord_progression=chord_progression,
            album_art_url=art_url,
            plagiarism_warning=warning,
        )
        self._songs[draft.id] = song
        if register_copyright and self.legal:
            self.legal.register_copyright(song.id, lyrics)


        # record initial version
        self.save_version(draft.id, creator_id, lyrics, chord_progression)
        self._counter += 1
        self.skill_service.add_songwriting_xp(creator_id)
        for i, a in enumerate(participants):
            for b in participants[i + 1 :]:
                self.chemistry_service.adjust_pair(a, b, 1)
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

        if chord_progression is not None:
            draft.chord_progression = chord_progression
            self._songs[draft_id].chord_progression = chord_progression
        if album_art_url is not None:
            draft.album_art_url = album_art_url
            self._songs[draft_id].album_art_url = album_art_url

        # save snapshot of updated state
        self.save_version(draft_id, user_id, draft.lyrics, draft.chord_progression, themes)
        self.skill_service.add_songwriting_xp(user_id, revised=True)

        return draft

    def add_co_writer(self, draft_id: int, user_id: int, co_writer_id: int) -> None:
        draft = self._drafts.get(draft_id)
        if not draft:
            raise KeyError("draft_not_found")
        if draft.creator_id != user_id and user_id not in self._co_writers.get(draft_id, set()):
            raise PermissionError("forbidden")
        if self.band_service and not self.band_service.share_band(user_id, co_writer_id):
            raise PermissionError("forbidden")
        self._co_writers.setdefault(draft_id, set()).add(co_writer_id)

    def save_version(
        self,
        draft_id: int,
        author_id: int,
        lyrics: str,
        chord_progression: Optional[str] = None,
        themes: Optional[List[str]] = None,
    ) -> SongDraftVersion:
        version = SongDraftVersion(
            author_id=author_id,
            lyrics=lyrics,
            chord_progression=chord_progression,
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


songwriting_service = SongwritingService(band_service=BandService())
