"""Service responsible for generating album art via AI."""
from __future__ import annotations

from typing import List

from backend.services.storage_service import get_storage_backend


class AIArtService:
    async def generate_album_art(self, title: str, themes: List[str]) -> str:
        """Generate album art and store using the storage backend.

        In this reference implementation we simply store a text placeholder
        representing the artwork. The storage backend returns a public URL
        which is then used by callers.
        """

        content = f"Album art for {title} about {', '.join(themes)}".encode()
        key = f"album_art/{title.replace(' ', '_').lower()}.txt"
        backend = get_storage_backend()
        obj = backend.upload_bytes(content, key, content_type="text/plain")
        return obj.url


ai_art_service = AIArtService()

