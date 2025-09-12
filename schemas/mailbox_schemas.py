from pydantic import BaseModel

class SendMailSchema(BaseModel):
    sender_id: int
    recipient_id: int
    subject: str
    message: str
    message_type: str

class ArchiveMailSchema(BaseModel):
    user_id: int
    message_index: int