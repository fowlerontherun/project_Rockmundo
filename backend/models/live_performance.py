from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class PerformanceAction(BaseModel):
    type: str  # 'song', 'speech', 'stunt', 'guest'
    reference: Optional[str]  # song_id or guest_band_id or description
    description: Optional[str]  # freeform notes (e.g. 'burns flag', 'calls out press')

class LivePerformance(BaseModel):
    id: int
    band_id: int
    venue_id: Optional[int]
    performance_type: str  # 'standard', 'acoustic', 'festival'
    date: date
    setlist: List[PerformanceAction]
    performance_score: float
    crowd_engagement: float
    fame_gain: float
    skill_gain: float
    revenue: float
    is_solo: bool