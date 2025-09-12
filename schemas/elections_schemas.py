from pydantic import BaseModel

class DeclareCandidateSchema(BaseModel):
    user_id: int
    role: str
    region: str
    manifesto: str

class CastVoteSchema(BaseModel):
    voter_id: int
    candidate_id: int
    role: str