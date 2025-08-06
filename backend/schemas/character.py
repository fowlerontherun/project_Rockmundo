from pydantic import BaseModel
from datetime import datetime

class CharacterBase(BaseModel):
    name: str
    genre: str
    trait: str
    birthplace: str

class CharacterCreate(CharacterBase):
    pass

class CharacterResponse(CharacterBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
