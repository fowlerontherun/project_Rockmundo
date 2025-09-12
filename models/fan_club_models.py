from pydantic import BaseModel
from typing import Optional

class FanClubCreate(BaseModel):
    band_id: int
    name: str
    description: Optional[str] = None
    premium_required: Optional[bool] = False

class FanClubJoin(BaseModel):
    user_id: int
    fan_club_id: int

class FanMissionCreate(BaseModel):
    fan_club_id: int
    title: str
    description: str
    reward: Optional[str] = None
