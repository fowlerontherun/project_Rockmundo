from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, List

from backend.models.video import Video
from backend.services.economy_service import EconomyService
from backend.services.media_moderation_service import media_moderation_service
from backend.services.skill_service import SkillService
from seeds.skill_seed import SEED_SKILLS
from backend.utils.metrics import _REGISTRY, Histogram

if "service_latency_ms" in _REGISTRY:
    SERVICE_LATENCY_MS = _REGISTRY["service_latency_ms"]  # type: ignore[assignment]
else:
    SERVICE_LATENCY_MS = Histogram(
        "service_latency_ms",
        "Service call latency in milliseconds",
        [50, 100, 250, 500, 1000, 2500, 5000],
        ("service", "operation"),
    )


CONTENT_CREATION_SKILL = next(
    s for s in SEED_SKILLS if s.name == "content_creation"
)
XP_PER_VIEW = 5


class VideoService:
    """Service layer handling video operations and monetization."""

    def __init__(
        self,
        economy: EconomyService,
        skill_service: SkillService | None = None,
        ad_rate_cents: int = 1,
    ):
        self.economy = economy
        self.skill_service = skill_service or SkillService()
        self.ad_rate_cents = ad_rate_cents
        self._videos: Dict[int, Video] = {}
        self._next_id = 1

    # -------------------- CRUD --------------------
    def upload_video(self, owner_id: int, title: str, filename: str) -> Video:
        # Ensure the title/filename do not contain disallowed terms
        media_moderation_service.ensure_clean(text=title, filename=filename)

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
        start = time.perf_counter()
        try:
            video = self._videos.get(video_id)
            if not video:
                raise KeyError(f"Video {video_id} not found")
            video.view_count += 1
            skill = self.skill_service._get_skill(
                video.owner_id, CONTENT_CREATION_SKILL
            )
            multiplier = 1 + skill.level / 100
            # Deposit ad revenue scaled by content creation skill
            self.economy.deposit(
                video.owner_id, int(self.ad_rate_cents * multiplier)
            )
            # Award XP for content creation
            self.skill_service.train(
                video.owner_id, CONTENT_CREATION_SKILL, XP_PER_VIEW
            )
            return video.view_count
        finally:
            SERVICE_LATENCY_MS.labels("video_service", "record_view").observe(
                (time.perf_counter() - start) * 1000
            )
