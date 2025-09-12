from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MediaEventBase(BaseModel):
    title: str
    type: str
    content: Optional[str] = None
    fame_impact: Optional[int] = 0

class MediaEventCreate(MediaEventBase):
    pass

class MediaEvent(MediaEventBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
