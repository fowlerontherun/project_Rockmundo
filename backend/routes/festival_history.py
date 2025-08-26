from auth.dependencies import get_current_user_id, require_role
from pydantic import BaseModel
from typing import List, Dict

class FestivalHistory(BaseModel):
    id: int
    festival_id: int
    year: int
    lineup: List[Dict[str, str]]  # [{band_id, stage, timeslot}]
    attendance: int
    ticket_sales: float
    revenue: float
    media_mentions: int
    reviews: List[str]