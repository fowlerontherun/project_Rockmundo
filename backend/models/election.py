from pydantic import BaseModel
from typing import List
from datetime import datetime

class Election(BaseModel):
    id: int
    role: str
    region: str
    candidates: List[int]
    votes: dict
    open: bool
    start_date: datetime
    end_date: datetime
    campaign_promises: dict