from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class FanClub(BaseModel):
    id: int
    artist_id: int
    name: str
    description: Optional[str]
    logo: Optional[str]
    creation_date: date
    membership_tiers: dict  # { 'casual': int, 'active': int, 'loyal': int, 'superfan': int }
    superfan_ids: List[int]
    exclusive_content_ids: List[int]
    fan_quests_enabled: bool
    voting_enabled: bool