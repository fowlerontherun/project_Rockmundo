from pydantic import BaseModel
from datetime import datetime

class AvatarBase(BaseModel):
    body_type: str
    skin_tone: str
    face_shape: str
    hair_style: str
    hair_color: str
    top_clothing: str
    bottom_clothing: str
    shoes: str
    accessory: str
    held_item: str
    pose: str

class AvatarCreate(AvatarBase):
    character_id: int

class AvatarResponse(AvatarBase):
    id: int
    character_id: int
    created_at: datetime

    class Config:
        orm_mode = True
