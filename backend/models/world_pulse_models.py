from pydantic import BaseModel
from typing import List, Dict

class GenreTrend(BaseModel):
    genre: str
    trend_score: float

class CityKarma(BaseModel):
    city: str
    avg_karma: int

class WorldEvent(BaseModel):
    description: str
    timestamp: str

class Influencer(BaseModel):
    band: str
    influence_score: float