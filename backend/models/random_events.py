# models/random_events.py

from pydantic import BaseModel
from typing import Optional
from datetime import date

class Event(BaseModel):
    id: int
    name: str
    type: str  # e.g., injury, illness, burnout
    effect_type: str  # e.g., block_skill, decay_skill, freeze_progress
    skill_affected: Optional[str] = None
    duration_days: int
    trigger_chance: float  # 0.01 = 1%

class ActiveEvent(BaseModel):
    id: int
    user_id: int
    event_id: int
    skill_affected: Optional[str]
    start_date: date
    duration_days: int
