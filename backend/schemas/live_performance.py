from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class PerformanceActionSchema(BaseModel):
    type: str
    reference: Optional[str]
    description: Optional[str]

class LivePerformanceCreate(BaseModel):
    band_id: int
    venue_id: Optional[int]
    performance_type: str
    date: date
    setlist: List[PerformanceActionSchema]
    is_solo: bool

class LivePerformanceResponse(LivePerformanceCreate):
    id: int
    performance_score: float
    crowd_engagement: float
    fame_gain: float
    skill_gain: float
    revenue: float