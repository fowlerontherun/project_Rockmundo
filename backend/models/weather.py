from datetime import date
from typing import Optional

from pydantic import BaseModel


class ClimateZone(BaseModel):
    """Represents a region and its overall climate pattern."""

    name: str
    pattern: str
    avg_high: float
    avg_low: float


class WeatherEvent(BaseModel):
    """Weather driven world events such as storms or festivals."""

    type: str
    severity: int
    description: Optional[str] = None


class Forecast(BaseModel):
    """Daily forecast for a region including optional events."""

    region: str
    date: date
    condition: str
    high: float
    low: float
    event: Optional[WeatherEvent] = None
