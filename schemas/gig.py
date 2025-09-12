from pydantic import BaseModel
from datetime import date, time
from typing import Optional

class GigCreate(BaseModel):
    band_id: int
    venue_id: int
    date: date
    start_time: time
    end_time: time
    ticket_price: float
    guarantee: float = 0.0
    ticket_split: float = 0.0
    expected_audience: int = 0
    support_band_id: Optional[int] = None
    promoted: Optional[bool] = False
    acoustic: Optional[bool] = False

class GigOut(BaseModel):
    id: int
    band_id: int
    venue_id: int
    date: date
    start_time: time
    end_time: time
    ticket_price: float
    guarantee: float
    ticket_split: float
    support_band_id: Optional[int]
    promoted: bool
    acoustic: bool
    audience_size: int
    total_earned: float
    xp_gained: int
    fans_gained: int
    review: Optional[str]

    class Config:
        orm_mode = True
