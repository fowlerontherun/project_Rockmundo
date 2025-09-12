from auth.dependencies import get_current_user_id, require_permission
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class Festival(BaseModel):
    id: int
    name: str
    country: str
    location: str
    type: str  # 'major', 'medium', 'player'
    created_by: Optional[int]
    start_date: date
    end_date: date
    season: str
    stage_count: int
    max_capacity: int
    cost: float
    headliners: List[int]
    full_lineup: List[int]
    ticket_price: float
    attendance: int
    revenue: float
    genre_focus: Optional[str]
    success_score: Optional[float]