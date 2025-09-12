from pydantic import BaseModel
from typing import Optional

class Emote(BaseModel):
    emote_id: str
    name: str
    category: str  # standard, stage, contextual
    unlocked_by: str  # fame, karma, skin, etc.
    cooldown: Optional[int] = 0  # seconds