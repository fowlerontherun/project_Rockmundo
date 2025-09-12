from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime

class ElectionCreate(BaseModel):
    role: str
    region: str
    candidates: List[int]
    start_date: datetime
    end_date: datetime
    campaign_promises: Dict[int, str]

class VoteCast(BaseModel):
    voter_id: int
    candidate_id: int