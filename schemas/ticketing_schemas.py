from pydantic import BaseModel

class TicketCreate(BaseModel):
    band_id: int
    venue_id: int
    price: float
    type: str
    fan_segment: str
    sold: int

class BookingReputationSchema(BaseModel):
    band_id: int
    score: float
    cancellations: int

class TicketEventSchema(BaseModel):
    ticket_id: int
    event_type: str
    description: str
