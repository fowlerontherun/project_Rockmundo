from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ReplayEvent(BaseModel):
    user_id: int
    event_id: str
    title: str
    description: str
    event_type: str  # gig, award, chart, etc.
    timestamp: datetime
    metadata: Optional[dict]