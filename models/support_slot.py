from pydantic import BaseModel
from typing import Optional

class SupportSlot(BaseModel):
    id: int
    main_band_id: int
    support_band_id: int
    tour_id: int
    status: str  # e.g., 'invited', 'accepted', 'declined'
    fee: Optional[float] = 0.0