from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class FanClubCreate(BaseModel):
    artist_id: int
    name: str
    description: Optional[str] = None
    logo: Optional[str] = None
    fan_quests_enabled: bool = False
    voting_enabled: bool = False

class FanClubResponse(FanClubCreate):
    id: int
    creation_date: date
    membership_tiers: dict
    superfan_ids: List[int]
    exclusive_content_ids: List[int]