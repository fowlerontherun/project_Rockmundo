from pydantic import BaseModel
from datetime import datetime

class SkinBase(BaseModel):
    name: str
    category: str
    mesh_url: str
    texture_url: str
    rarity: str
    author: str
    price: int

class SkinCreate(SkinBase):
    pass

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
