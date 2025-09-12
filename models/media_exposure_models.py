from pydantic import BaseModel
from typing import Optional

class SocialMediaPost(BaseModel):
    band_id: int
    platform: str  # FauxTube, TikkaTok, Bandr
    content: str
    views: Optional[int] = 0
    likes: Optional[int] = 0
    created_at: Optional[str] = None

class PodcastAppearance(BaseModel):
    band_id: int
    podcast_name: str
    topic: str
    scheduled_at: Optional[str] = None
