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
