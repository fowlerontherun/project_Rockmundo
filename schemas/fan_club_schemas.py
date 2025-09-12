from pydantic import BaseModel

class FanClubCreateSchema(BaseModel):
    band_id: int
    name: str
    description: str
    premium_required: bool

class FanClubJoinSchema(BaseModel):
    user_id: int
    fan_club_id: int

class FanMissionSchema(BaseModel):
    fan_club_id: int
    title: str
    description: str
    reward: str
