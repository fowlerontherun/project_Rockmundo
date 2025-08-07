from pydantic import BaseModel
from datetime import date

class SalesCreate(BaseModel):
    song_id: int
    date: date
    format: str
    units_sold: int
    revenue: float
    production_cost: float