"""Simple content moderation utilities for dialogue outputs."""
from __future__ import annotations

import re
from typing import Iterable

# Minimal list of banned words for demonstration/testing purposes.
BANNED_WORDS: Iterable[str] = ["violence", "kill", "murder"]
REPLACEMENT = "[filtered]"


def moderate_content(text: str) -> str:
    """Return text with banned words replaced."""
    if not text:
        return text
    result = text
    for word in BANNED_WORDS:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        result = pattern.sub(REPLACEMENT, result)
    return result


def is_clean(text: str) -> bool:
    """Quick check if text contains banned words."""
    lowered = text.lower()
    return not any(word in lowered for word in BANNED_WORDS)
