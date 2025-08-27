"""Models for AI-assisted songwriting drafts and metadata."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class GenerationMetadata:
    """Metadata about an LLM generation."""

    model: str = "unknown"
    latency_ms: Optional[int] = None


@dataclass
class StylePrompt:
    """Describes the desired musical style for generation."""

    genre: str
    mood: Optional[str] = None
    tempo: Optional[str] = None


@dataclass
class LyricDraft:
    """A single AI generated lyric draft with optional chords."""

    id: int
    creator_id: int
    prompt: str
    style: str
    lyrics: str
    chords: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: GenerationMetadata = field(default_factory=GenerationMetadata)
