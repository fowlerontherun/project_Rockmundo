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
    nutrition: float = 70.0
    fitness: float = 70.0
    appearance_score: float = 50.0
    exercise_minutes: float = 0.0
    last_exercise: Optional[str] = None
    lifestyle_score: Optional[float] = None
