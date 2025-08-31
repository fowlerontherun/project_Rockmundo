from enum import Enum
from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class PerformanceActionType(str, Enum):
    song = "song"
    activity = "activity"
    encore = "encore"


class PerformanceActionSchema(BaseModel):
    type: PerformanceActionType
    reference: Optional[str]
    description: Optional[str]
    duration: Optional[int] = None
    position: Optional[int] = None
    encore: Optional[bool] = False


class LivePerformanceCreate(BaseModel):
    band_id: int
    venue_id: Optional[int]
    performance_type: str
    date: date
    setlist: List[PerformanceActionSchema]
    encore: Optional[List[PerformanceActionSchema]] = None
    is_solo: bool


class LivePerformanceResponse(LivePerformanceCreate):
    id: int
    performance_score: float
    crowd_engagement: float
    fame_gain: float
    skill_gain: float
    revenue: float

