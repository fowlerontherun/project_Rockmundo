# models/lifestyle.py

from pydantic import BaseModel
from typing import Optional

class Lifestyle(BaseModel):
    user_id: int
    sleep_hours: float = 7.0
    drinking: str = "none"  # options: none, light, moderate, heavy
    stress: float = 0.0
    training_discipline: float = 50.0
    mental_health: float = 100.0
    lifestyle_score: Optional[float] = None
