from pydantic import BaseModel

class EmoteTriggerSchema(BaseModel):
    user_id: int
    emote_id: str
    context: str  # gig, crowd, awards, social