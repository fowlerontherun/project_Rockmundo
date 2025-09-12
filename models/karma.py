from pydantic import BaseModel
from datetime import datetime

class KarmaEvent(BaseModel):
    id: int
    user_id: int
    score_change: int
    reason: str
    timestamp: datetime
    auto: bool = False  # whether the change was automatic
    visible_reason: str = ""