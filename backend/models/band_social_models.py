from pydantic import BaseModel
from typing import List, Optional

class Alliance(BaseModel):
    id: int
    name: str
    leader_band_id: int
    members: List[int] = []

class Rivalry(BaseModel):
    id: int
    band_1_id: int
    band_2_id: int
    intensity: int