from pydantic import BaseModel


class SkinPurchaseRequest(BaseModel):
    avatar_id: int


class SkinApplyRequest(BaseModel):
    avatar_id: int


class SkinUploadRequest(BaseModel):
    name: str
    category: str
    rarity: str
    author: str
    price: int
    mesh_b64: str
    texture_b64: str
