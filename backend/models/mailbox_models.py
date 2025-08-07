from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Mail(BaseModel):
    sender_id: int
    recipient_id: int
    subject: str
    message: str
    message_type: Optional[str] = "system"  # system, player, ai, fan, booking
    timestamp: datetime
    archived: bool = False