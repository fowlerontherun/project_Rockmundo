from typing import Optional

from backend.services.song_popularity_service import SongPopularityService, song_popularity_service


class MediaEventService:
    """Register media exposure events affecting song popularity."""

    def __init__(self, popularity_svc: Optional[SongPopularityService] = None):
        self.popularity_svc = popularity_svc or song_popularity_service

    def film_placement(
        self,
        song_id: int,
        boost: int = 20,
        region_code: str = "global",
        platform: str = "any",
    ):
        return self._register(song_id, "film", boost, region_code, platform)

    def tv_placement(
        self,
        song_id: int,
        boost: int = 15,
        region_code: str = "global",
        platform: str = "any",
    ):
        return self._register(song_id, "tv", boost, region_code, platform)

    def tiktok_trend(
        self,
        song_id: int,
        boost: int = 30,
        region_code: str = "global",
        platform: str = "any",
    ):
        return self._register(song_id, "tiktok", boost, region_code, platform)

    def _register(
        self, song_id: int, source: str, boost: int, region_code: str, platform: str
    ):
        return self.popularity_svc.add_event(song_id, source, boost, region_code, platform)


media_event_service = MediaEventService()
