from pydantic import BaseModel
from typing import List, Optional

class Message(BaseModel):
    sender_id: int
    recipient_id: int
    content: str
    timestamp: str

class GroupMessage(BaseModel):
    sender_id: int
    group_id: str
    content: str
    timestamp: str