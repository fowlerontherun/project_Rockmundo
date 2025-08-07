from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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