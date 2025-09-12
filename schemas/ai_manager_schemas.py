from pydantic import BaseModel

class AIActivationSchema(BaseModel):
    band_id: int
    type: str
    persona: str

class AIOverrideSchema(BaseModel):
    band_id: int
    action: str