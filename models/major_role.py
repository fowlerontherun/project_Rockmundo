from pydantic import BaseModel
from typing import List, Optional

class Major(BaseModel):
    id: int
    name: str
    description: str
    members: List[int] = []
    leader_id: Optional[int] = None
    perks: Optional[str] = None

class RoleAssignment(BaseModel):
    user_id: int
    major_id: int
    role: str