from pydantic import BaseModel
from typing import Optional

class LogReplayEventSchema(BaseModel):
    user_id: int
    event_id: str
    title: str
    description: str
    event_type: str
    metadata: Optional[dict]

class ReplayEventRequestSchema(BaseModel):
    user_id: int
    event_id: str