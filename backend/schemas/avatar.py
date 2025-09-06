from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


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
    stamina: int = 50
    charisma: int = 50
    intelligence: int = 50
    creativity: int = 50
    discipline: int = 50
    luck: int = 0


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
    stamina: Optional[int] = None
    charisma: Optional[int] = None
    intelligence: Optional[int] = None
    creativity: Optional[int] = None
    discipline: Optional[int] = None
    luck: Optional[int] = None

    @field_validator(
        "stamina",
        "charisma",
        "intelligence",
        "creativity",
        "discipline",
        "luck",
    )
    @classmethod
    def _validate_stats(cls, v: int | None) -> int | None:
        if v is not None and not 0 <= v <= 100:
            raise ValueError("must be between 0 and 100")
        return v


class AvatarResponse(AvatarBase):
    id: int
    character_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
