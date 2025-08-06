from pydantic import BaseModel
from typing import Optional

class DistributionUpdate(BaseModel):
    song_id: int
    streams: Optional[int] = 0
    digital_sales: Optional[int] = 0
    vinyl_sales: Optional[int] = 0
    digital_cost: Optional[float] = 0.0
    vinyl_cost: Optional[float] = 0.0

class DistributionResponse(BaseModel):
    song_id: int
    streams: int
    digital_sales: int
    vinyl_sales: int
    digital_revenue: float
    vinyl_revenue: float
    streaming_revenue: float

    class Config:
        orm_mode = True
