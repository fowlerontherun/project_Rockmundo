from pydantic import BaseModel
from typing import Optional
from datetime import date

class Endorsement(BaseModel):
    id: int
    artist_id: int
    brand_name: str
    product_type: str  # e.g., 'guitar', 'clothing', 'mic'
    deal_value: float
    start_date: date
    end_date: Optional[date]
    active: bool