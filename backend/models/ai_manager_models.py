from pydantic import BaseModel
from typing import List, Optional

class AIManagerProfile(BaseModel):
    band_id: int
    type: str  # tour, pr, media, release, persona
    persona: Optional[str] = "neutral"  # aggressive, friendly, growth-focused, etc.
    active: bool = True

class AISuggestion(BaseModel):
    suggestion_type: str
    content: str
    impact_estimate: Optional[str] = None