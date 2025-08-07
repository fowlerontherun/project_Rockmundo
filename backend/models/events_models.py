from pydantic import BaseModel
from typing import List, Optional

class SeasonalEvent(BaseModel):
    event_id: str
    name: str
    theme: str
    description: str
    active: bool
    start_date: str
    end_date: Optional[str] = None
    modifiers: dict