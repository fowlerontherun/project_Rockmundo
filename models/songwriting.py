"""Models for AI-assisted songwriting drafts and metadata."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class GenerationMetadata:
    """Metadata about an LLM generation."""

    model: str = "unknown"
    latency_ms: Optional[int] = None
    quality_modifier: float = 1.0
    chemistry: Optional[float] = None


@dataclass
class LyricDraft:
    """A single AI generated songwriting draft."""

    id: int
    creator_id: int
    title: str
    genre: str
    themes: List[str]
    lyrics: str
    chord_progression: str
    album_art_url: Optional[str] = None
    plagiarism_warning: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: GenerationMetadata = field(default_factory=GenerationMetadata)
    status: str = "draft"
    completed_at: Optional[datetime] = None
    writing_minutes: int = 60
    revision_sessions: int = 0
    quality_score: Optional[int] = None
    polish_available: bool = False
    polish_attempted: bool = False
    polish_success_chance: Optional[int] = None
    polish_succeeded: Optional[bool] = None
    polish_skipped: bool = False
    polish_bonus: int = 0
