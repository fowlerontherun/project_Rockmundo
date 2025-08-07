from pydantic import BaseModel

class KarmaEventCreate(BaseModel):
    user_id: int
    score_change: int
    reason: str
    auto: bool = False
    visible_reason: str = ""