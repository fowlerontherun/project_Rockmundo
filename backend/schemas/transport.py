from pydantic import BaseModel

class TransportCreate(BaseModel):
    name: str
    capacity: int
    speed: float
    fuel_cost_per_km: float
    sleep_quality: float
    maintenance_cost: float
    travel_range_km: int
    type: str  # e.g., 'van', 'bus', 'plane', etc.