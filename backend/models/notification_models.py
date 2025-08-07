from pydantic import BaseModel
from typing import Optional

class Notification(BaseModel):
    user_id: int
    message: str
    type: Optional[str] = "info"
    timestamp: Optional[str]

class ScheduledEvent(BaseModel):
    user_id: int
    event_type: str
    description: str
    scheduled_time: str