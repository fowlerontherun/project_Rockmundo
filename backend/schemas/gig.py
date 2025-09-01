from pydantic import BaseModel
from datetime import date
from typing import Optional

class GigCreate(BaseModel):
    band_id: int
    venue_id: int
    date: date
    ticket_price: float
    support_band_id: Optional[int] = None
    promoted: Optional[bool] = False
    acoustic: Optional[bool] = False

class GigOut(BaseModel):
    id: int
    band_id: int
    venue_id: int
    date: date
    ticket_price: float
    support_band_id: Optional[int]
    promoted: bool
    acoustic: bool
    audience_size: int
    total_earned: float
    review: Optional[str]

    class Config:
        orm_mode = True
