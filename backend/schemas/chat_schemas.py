from pydantic import BaseModel

class MessageSchema(BaseModel):
    sender_id: int
    recipient_id: int
    content: str

class GroupMessageSchema(BaseModel):
    sender_id: int
    group_id: str
    content: str