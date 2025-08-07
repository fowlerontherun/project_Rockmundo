from pydantic import BaseModel
from typing import Optional
from datetime import date

class Promotion(BaseModel):
    id: int
    band_id: int
    type: str  # 'radio' | 'tv' | 'stream' | 'article' | 'stunt' | 'podcast' | 'youtube' | 'tiktok'
    date: date
    outcome: str  # 'positive' | 'neutral' | 'negative'
    fame_change: float
    fan_gain: int
    press_score_change: float
    controversy_level: float
    media_channel: Optional[str]