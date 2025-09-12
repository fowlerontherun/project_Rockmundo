from pydantic import BaseModel
from datetime import date

class TourCreate(BaseModel):
    band_id: int
    name: str
    start_date: date

class TourStopCreate(BaseModel):
    tour_id: int
    city_id: int
    venue_id: int
    date: date