from pydantic import BaseModel
from typing import Optional

class CreateEventSchema(BaseModel):
    event_id: str
    name: str
    theme: str
    description: str
    start_date: str
    modifiers: dict

class EndEventSchema(BaseModel):
    event_id: str