from pydantic import BaseModel


class SkinPurchaseRequest(BaseModel):
    avatar_id: int


class SkinApplyRequest(BaseModel):
    avatar_id: int
