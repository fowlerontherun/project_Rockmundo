"""Service for generating weather forecasts and world events."""
from __future__ import annotations

import random
from datetime import date
from typing import Dict, List, Optional

from backend.models.weather import ClimateZone, Forecast, WeatherEvent


class WeatherService:
    def __init__(self, zones: Optional[Dict[str, ClimateZone]] = None) -> None:
        self.zones: Dict[str, ClimateZone] = zones or {}
        self.subscribers: Dict[str, List[int]] = {}

    # --------- zone management ---------
    def add_zone(self, zone: ClimateZone) -> None:
        self.zones[zone.name] = zone

    # --------- forecasting ---------
    def get_forecast(self, region: str, for_date: Optional[date] = None) -> Forecast:
        zone = self.zones.get(region)
        if not zone:
            zone = ClimateZone(name=region, pattern="temperate", avg_high=25, avg_low=15)
        high = random.randint(int(zone.avg_high - 5), int(zone.avg_high + 5))
        low = random.randint(int(zone.avg_low - 5), int(zone.avg_low + 5))
        condition = random.choice(["sunny", "cloudy", "rain"])
        event: Optional[WeatherEvent] = None
        roll = random.random()
        if roll < 0.1:
            event = WeatherEvent(type="storm", severity=random.randint(1, 10))
        elif roll < 0.15:
            event = WeatherEvent(type="festival", severity=random.randint(1, 10))
        return Forecast(region=region, date=for_date or date.today(), condition=condition, high=high, low=low, event=event)

    # --------- subscriptions ---------
    def subscribe(self, region: str, user_id: int) -> None:
        self.subscribers.setdefault(region, []).append(user_id)


weather_service = WeatherService()
