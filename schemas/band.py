from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class BandCreate(BaseModel):
    name: str
    founder_id: int
    genre: str

class BandResponse(BaseModel):
    id: int
    name: str
    founder_id: int
    genre: str
    formed_at: datetime

    class Config:
        orm_mode = True

class BandMemberInvite(BaseModel):
    character_id: int
    band_id: int
    role: str
    is_manager: Optional[bool] = False

class BandCollaborationCreate(BaseModel):
    band_1_id: int
    band_2_id: int
    project_type: str  # "song" or "album"
    title: str

class BandCollaborationResponse(BandCollaborationCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
