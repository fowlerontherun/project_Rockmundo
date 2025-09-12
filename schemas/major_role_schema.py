from pydantic import BaseModel
from typing import Optional

class MajorCreate(BaseModel):
    name: str
    description: str
    perks: Optional[str] = None

class RoleAssignmentCreate(BaseModel):
    user_id: int
    major_id: int
    role: str