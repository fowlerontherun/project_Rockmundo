from pydantic import BaseModel
from typing import Optional
from datetime import date

class PromotionCreate(BaseModel):
    band_id: int
    type: str
    date: date
    media_channel: Optional[str]

class PromotionResponse(PromotionCreate):
    id: int
    outcome: str
    fame_change: float
    fan_gain: int
    press_score_change: float
    controversy_level: float