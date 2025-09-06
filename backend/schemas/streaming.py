from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DigitalSaleCreate(BaseModel):
    song_id: int
    buyer_id: int
    price: float


class VinylSaleCreate(BaseModel):
    album_id: int
    buyer_id: int
    price: float
    production_cost: float


class StreamCreate(BaseModel):
    song_id: int
    listener_id: int
    region: Optional[str]
    platform: Optional[str]


class DigitalSaleOut(DigitalSaleCreate):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True


class VinylSaleOut(VinylSaleCreate):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True


class StreamOut(StreamCreate):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True


class LiveStreamRequest(BaseModel):
    duration_minutes: int
    viewers: int = 100


class LiveStreamResult(BaseModel):
    retained_viewers: int
    tips: float
    skill_level: int


__all__ = [
    "DigitalSaleCreate",
    "VinylSaleCreate",
    "StreamCreate",
    "DigitalSaleOut",
    "VinylSaleOut",
    "StreamOut",
    "LiveStreamRequest",
    "LiveStreamResult",
]

