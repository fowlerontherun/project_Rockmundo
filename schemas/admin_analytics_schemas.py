from pydantic import BaseModel
from typing import Optional

class AnalyticsFilterSchema(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    region: Optional[str] = None
    platform: Optional[str] = None
    npc_only: Optional[bool] = False