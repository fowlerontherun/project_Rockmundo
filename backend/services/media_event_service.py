from typing import Optional

from backend.services.song_popularity_service import song_popularity_service, SongPopularityService


class MediaEventService:
    """Register media exposure events affecting song popularity."""

    def __init__(self, popularity_svc: Optional[SongPopularityService] = None):
        self.popularity_svc = popularity_svc or song_popularity_service

    def film_placement(self, song_id: int, boost: int = 20):
        return self._register(song_id, "film", boost)

    def tv_placement(self, song_id: int, boost: int = 15):
        return self._register(song_id, "tv", boost)

    def tiktok_trend(self, song_id: int, boost: int = 30):
        return self._register(song_id, "tiktok", boost)

    def _register(self, song_id: int, source: str, boost: int):
        return self.popularity_svc.add_event(song_id, source, boost)


media_event_service = MediaEventService()
