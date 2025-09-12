from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MusicLabel(BaseModel):
    label_id: str
    name: str
    owner_id: Optional[int]
    founded: datetime
    fame: int
    is_npc: bool

class LabelContract(BaseModel):
    contract_id: str
    label_id: str
    band_id: int
    revenue_split: float
    duration_weeks: int
    signed_on: datetime
    active: bool