"""Simple in-memory originality checker for lyrics."""
from __future__ import annotations

import hashlib
from typing import Dict, Tuple

from backend.models.lyric_hash import LyricHash


class OriginalityService:
    """Hashes lyrics and detects duplicates."""

    def __init__(self) -> None:
        self._hashes: Dict[str, LyricHash] = {}
        self._counter = 1

    def register_lyrics(self, lyrics: str, song_id: int) -> Tuple[LyricHash, bool]:
        """Store hash for lyrics and indicate if it already existed."""

        digest = hashlib.sha256(lyrics.encode("utf-8")).hexdigest()
        existing = self._hashes.get(digest)
        if existing:
            return existing, True
        record = LyricHash(id=self._counter, song_id=song_id, hash=digest)
        self._hashes[digest] = record
        self._counter += 1
        return record, False


originality_service = OriginalityService()
