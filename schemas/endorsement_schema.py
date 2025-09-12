from pydantic import BaseModel
from typing import Optional
from datetime import date

class EndorsementCreate(BaseModel):
    artist_id: int
    brand_name: str
    product_type: str
    deal_value: float
    end_date: Optional[date] = None

class EndorsementResponse(EndorsementCreate):
    id: int
    start_date: date
    active: bool