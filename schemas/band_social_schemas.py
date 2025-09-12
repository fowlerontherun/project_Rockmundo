from pydantic import BaseModel
from typing import List

class AllianceCreateSchema(BaseModel):
    name: str
    leader_band_id: int

class RivalryDeclareSchema(BaseModel):
    band_1_id: int
    band_2_id: int