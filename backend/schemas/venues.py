from pydantic import BaseModel

class VenueCreate(BaseModel):
    name: str
    city_id: int
    capacity: int
    fame_multiplier: float