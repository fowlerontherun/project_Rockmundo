from pydantic import BaseModel
from typing import Optional

class PressEventCreateSchema(BaseModel):
    headline: str
    description: str
    type: str
    fame_impact: int

class StatementSchema(BaseModel):
    band_id: int
    content: str
    sentiment: Optional[str] = "neutral"