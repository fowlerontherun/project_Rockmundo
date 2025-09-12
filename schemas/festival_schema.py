from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class FestivalCreate(BaseModel):
    name: str
    country: str
    location: str
    type: str
    start_date: date
    end_date: date
    stage_count: int
    max_capacity: int
    cost: float
    ticket_price: float
    genre_focus: Optional[str]

class FestivalResponse(FestivalCreate):
    id: int
    attendance: int
    revenue: float
    success_score: Optional[float]