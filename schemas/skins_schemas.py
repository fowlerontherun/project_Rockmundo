from pydantic import BaseModel

class SubmitSkinSchema(BaseModel):
    name: str
    creator_id: int
    type: str
    image_url: str
    description: str
    price: float

class VoteSkinSchema(BaseModel):
    user_id: int
    skin_name: str
    vote_type: str

class PurchaseSkinSchema(BaseModel):
    user_id: int
    skin_name: str