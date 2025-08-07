from pydantic import BaseModel

class SocialMediaPostSchema(BaseModel):
    band_id: int
    platform: str
    content: str

class PodcastAppearanceSchema(BaseModel):
    band_id: int
    podcast_name: str
    topic: str
