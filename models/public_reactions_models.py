from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PressEvent(BaseModel):
    id: int
    headline: str
    description: str
    type: str
    fame_impact: int
    timestamp: datetime

class PublicReputation(BaseModel):
    band_id: int
    reputation_status: str
    last_updated: datetime