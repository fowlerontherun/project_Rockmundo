from pydantic import BaseModel
from typing import Optional

class Skin(BaseModel):
    name: str
    creator_id: int
    type: str
    image_url: str
    description: Optional[str] = ""
    status: str = "pending"
    price: float = 0.0
    votes: int = 0

class Vote(BaseModel):
    user_id: int
    skin_name: str
    vote_type: str

class Purchase(BaseModel):
    user_id: int
    skin_name: str