from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SkinBase(BaseModel):
    name: str
    category: str
    mesh_url: str
    texture_url: str
    rarity: str
    author: str
    price: int


class SkinCreate(SkinBase):
    """Schema for creating new skins."""

    pass


class SkinUpdate(BaseModel):
    """Schema for updating existing skins.

    All fields are optional so callers may perform partial updates.
    """

    name: Optional[str] = None
    category: Optional[str] = None
    mesh_url: Optional[str] = None
    texture_url: Optional[str] = None
    rarity: Optional[str] = None
    author: Optional[str] = None
    price: Optional[int] = None
    is_approved: Optional[bool] = None
    is_official: Optional[bool] = None

class SkinResponse(SkinBase):
    id: int
    is_approved: bool
    is_official: bool
    created_at: datetime

    class Config:
        orm_mode = True

class SkinEquipRequest(BaseModel):
    character_id: int
    skin_id: int
    slot: str  # e.g. top, bottom, guitar

class SkinInventoryItem(BaseModel):
    skin: SkinResponse
    is_equipped: bool
    slot: str
    equipped_at: datetime

    class Config:
        orm_mode = True
