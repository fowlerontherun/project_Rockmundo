import re
from typing import Callable, Dict, List

from backend.services.song_popularity_service import song_popularity_service


class MediaMonitorService:
    """Monitor external media feeds and boost song popularity on mentions."""

    def __init__(
        self, feed_source: Callable[[], List[str]] | None = None, default_boost: int = 5
    ) -> None:
        self.feed_source = feed_source or (lambda: [])
        self.default_boost = default_boost

    def poll_feed(self) -> List[Dict]:
        """Fetch the feed and register any song_id mentions."""
        items = self.feed_source()
        found: List[Dict] = []
        for item in items:
            match = re.search(r"song_id:(\d+)", item)
            if not match:
                continue
            song_id = int(match.group(1))
            song_popularity_service.add_event(
                song_id, "media", self.default_boost, details=item
            )
            found.append({"song_id": song_id, "details": item})
        return found

    def manual_adjust(self, song_id: int, amount: int, details: str = "") -> Dict:
        """Apply a manual popularity adjustment."""
        song_popularity_service.add_event(
            song_id, "media_manual", amount, details=details
        )
        return {"song_id": song_id, "amount": amount}


media_monitor_service = MediaMonitorService()
