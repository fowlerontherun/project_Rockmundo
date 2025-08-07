from pydantic import BaseModel
from datetime import date

class ChartEntryCreate(BaseModel):
    date: date
    chart_type: str
    category: str
    song_id: int
    rank: int