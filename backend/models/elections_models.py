from pydantic import BaseModel
from typing import Optional

class Candidate(BaseModel):
    user_id: int
    role: str
    region: Optional[str]
    manifesto: str

class Vote(BaseModel):
    voter_id: int
    candidate_id: int
    role: str