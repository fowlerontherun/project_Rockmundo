from pydantic import BaseModel
from typing import Optional

class LabelCreateSchema(BaseModel):
    label_id: str
    name: str
    owner_id: Optional[int]
    is_npc: Optional[bool] = True

class ContractOfferSchema(BaseModel):
    contract_id: str
    label_id: str
    band_id: int
    revenue_split: float
    duration_weeks: int