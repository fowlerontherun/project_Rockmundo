from pydantic import BaseModel
from typing import Optional

class SupportSlotCreate(BaseModel):
    main_band_id: int
    support_band_id: int
    tour_id: int
    fee: Optional[float] = 0.0

class SupportSlotResponse(SupportSlotCreate):
    id: int
    status: str