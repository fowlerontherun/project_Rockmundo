"""Utilities for scanning uploaded media for disallowed content."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from backend.services.moderation_service import (
    BANNED_WORDS as TEXT_BANNED_WORDS,
    moderate_content,
)


@dataclass
class ModerationResult:
    """Structured result from a moderation scan."""

    allowed: bool
    reasons: List[str]


class MediaModerationService:
    """Scan media payloads for banned terms.

    The implementation is intentionally lightweight – it simply looks for the
    same banned words used by the text moderation utilities. This is sufficient
    for the unit tests and mirrors how a real system might delegate to an
    external moderation provider.
    """

    def __init__(self, banned_words: Iterable[str] | None = None) -> None:
        self.banned_words = [w.lower() for w in (banned_words or TEXT_BANNED_WORDS)]

    # ------------------------------------------------------------------
    # Scanning helpers
    def scan_bytes(self, data: bytes) -> ModerationResult:
        """Check raw bytes for banned words."""

        lowered = data.lower()
        reasons = [word for word in self.banned_words if word.encode() in lowered]
        return ModerationResult(allowed=not reasons, reasons=reasons)

    def scan_text(self, text: str) -> ModerationResult:
        """Check a text string for banned words."""

        lowered = text.lower()
        reasons = [word for word in self.banned_words if word in lowered]
        return ModerationResult(allowed=not reasons, reasons=reasons)

    # ------------------------------------------------------------------
    def filter_text(self, text: str) -> str:
        """Apply text filtering using the existing moderation utilities."""

        return moderate_content(text)

    def check(
        self,
        *,
        data: bytes | None = None,
        text: str | None = None,
        filename: str | None = None,
    ) -> ModerationResult:
        """Run moderation checks on any provided fields."""

        reasons: List[str] = []

        if data is not None:
            res = self.scan_bytes(data)
            reasons.extend(res.reasons)

        for field in (text, filename):
            if field:
                res = self.scan_text(field)
                reasons.extend(res.reasons)

        # Deduplicate reasons while preserving order
        deduped = list(dict.fromkeys(reasons))
        return ModerationResult(allowed=not deduped, reasons=deduped)

    def ensure_clean(
        self,
        *,
        data: bytes | None = None,
        text: str | None = None,
        filename: str | None = None,
    ) -> ModerationResult:
        """Raise ``ValueError`` if disallowed content is detected."""

        result = self.check(data=data, text=text, filename=filename)
        if not result.allowed:
            raise ValueError(
                "Disallowed content: " + ", ".join(result.reasons)
            )
        return result


# Shared instance used by other services
media_moderation_service = MediaModerationService()

