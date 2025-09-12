from pydantic import BaseModel

class NotificationSchema(BaseModel):
    user_id: int
    message: str
    type: str

class ScheduleEventSchema(BaseModel):
    user_id: int
    event_type: str
    description: str
    scheduled_time: str