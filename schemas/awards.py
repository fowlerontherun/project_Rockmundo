from pydantic import BaseModel
from datetime import date

class SongAwardCreate(BaseModel):
    song_id: int
    award_name: str
    date_awarded: date
    details: str = None