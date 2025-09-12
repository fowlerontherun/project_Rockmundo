from pydantic import BaseModel
from typing import List

class TutorialStep(BaseModel):
    user_id: int
    step: str
    completed: bool

class Tip(BaseModel):
    stage: str
    content: str