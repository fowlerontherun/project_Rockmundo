from pydantic import BaseModel
from typing import Optional
from datetime import date

class Manager(BaseModel):
    id: int
    name: str
    artist_id: int
    type: str  # e.g., 'personal', 'tour', 'business'
    hire_date: date
    salary: float
    active: bool