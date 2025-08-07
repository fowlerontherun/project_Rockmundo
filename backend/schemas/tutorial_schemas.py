from pydantic import BaseModel

class StartTutorialSchema(BaseModel):
    user_id: int

class CompleteStepSchema(BaseModel):
    user_id: int
    step: str

class TipRequestSchema(BaseModel):
    stage: str