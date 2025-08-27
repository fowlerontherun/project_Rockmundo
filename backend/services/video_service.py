from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from backend.models.video import Video
from backend.services.economy_service import EconomyService


class VideoService:
    """Service layer handling video operations and monetization."""

    def __init__(self, economy: EconomyService, ad_rate_cents: int = 1):
        self.economy = economy
        self.ad_rate_cents = ad_rate_cents
        self._videos: Dict[int, Video] = {}
        self._next_id = 1

    # -------------------- CRUD --------------------
    def upload_video(self, owner_id: int, title: str, filename: str) -> Video:
        video = Video(
            id=self._next_id,
            owner_id=owner_id,
            title=title,
            filename=filename,
            uploaded_at=datetime.utcnow(),
            status="processing",
        )
        self._videos[video.id] = video
        self._next_id += 1
        return video

    def mark_transcoded(self, video_id: int) -> None:
        video = self._videos.get(video_id)
        if video:
            video.status = "ready"

    def get_video(self, video_id: int) -> Video | None:
        return self._videos.get(video_id)

    def list_videos(self) -> List[Video]:
        return list(self._videos.values())

    def delete_video(self, video_id: int) -> None:
        self._videos.pop(video_id, None)

    # -------------------- metrics --------------------
    def record_view(self, video_id: int) -> int:
        video = self._videos.get(video_id)
        if not video:
            raise KeyError(f"Video {video_id} not found")
        video.view_count += 1
        # Deposit ad revenue to the owner
        self.economy.deposit(video.owner_id, self.ad_rate_cents)
        return video.view_count
