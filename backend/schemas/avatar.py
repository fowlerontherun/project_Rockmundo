from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AvatarBase(BaseModel):
    """Shared avatar attributes."""

    nickname: str
    body_type: str
    skin_tone: str
    face_shape: str
    hair_style: str
    hair_color: str
    top_clothing: str
    bottom_clothing: str
    shoes: str
    accessory: Optional[str] = None
    held_item: Optional[str] = None
    pose: Optional[str] = None

    # Basic stats
    level: int = 1
    experience: int = 0
    health: int = 100
    mood: int = 50


class AvatarCreate(AvatarBase):
    character_id: int


class AvatarUpdate(BaseModel):
    """Fields that can be updated."""

    nickname: Optional[str] = None
    body_type: Optional[str] = None
    skin_tone: Optional[str] = None
    face_shape: Optional[str] = None
    hair_style: Optional[str] = None
    hair_color: Optional[str] = None
    top_clothing: Optional[str] = None
    bottom_clothing: Optional[str] = None
    shoes: Optional[str] = None
    accessory: Optional[str] = None
    held_item: Optional[str] = None
    pose: Optional[str] = None
    level: Optional[int] = None
    experience: Optional[int] = None
    health: Optional[int] = None
    mood: Optional[int] = None


class AvatarResponse(AvatarBase):
    id: int
    character_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
