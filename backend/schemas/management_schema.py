from pydantic import BaseModel
from typing import Optional
from datetime import date

class ManagerCreate(BaseModel):
    name: str
    artist_id: int
    type: str
    salary: float

class ManagerResponse(ManagerCreate):
    id: int
    hire_date: date
    active: bool