"""Service for managing city economic trends and analytics."""
from __future__ import annotations

import random
from typing import Dict, List

from backend.models.city import City


class CityService:
    """Maintain cities and update their market trends daily."""

    def __init__(self) -> None:
        self.cities: Dict[str, City] = {}
        self.day: int = 0

    # ------------ city management ------------
    def add_city(self, city: City) -> None:
        self.cities[city.name] = city

    def get_city(self, name: str) -> City | None:
        return self.cities.get(name)

    # ------------ economics ------------
    def update_daily(self) -> None:
        """Advance the simulation by one day updating trends."""
        self.day += 1
        for city in self.cities.values():
            delta = random.uniform(-0.05, 0.05)
            city.market_index = max(0.1, city.market_index * (1 + delta))
            # adjust style preferences slightly
            for style, pref in list(city.style_preferences.items()):
                city.style_preferences[style] = max(0.0, pref + random.uniform(-0.1, 0.1))
            # event modifier derived from market index
            city.event_modifier = 1 + (city.market_index - 1) * 0.2

    def get_event_modifier(self, name: str) -> float:
        city = self.cities.get(name)
        return city.event_modifier if city else 1.0

    def get_market_demand(self, name: str) -> float:
        city = self.cities.get(name)
        return city.market_index if city else 1.0

    # ------------ analytics ------------
    def stats(self, name: str) -> Dict[str, object]:
        city = self.cities.get(name)
        if not city:
            raise KeyError(name)
        return {
            "name": city.name,
            "population": city.population,
            "market_index": city.market_index,
            "popular_style": city.popular_style(),
        }

    def popular_cities(self, limit: int = 5) -> List[Dict[str, object]]:
        """Return top cities sorted by market index."""
        data = [self.stats(n) for n in self.cities]
        data.sort(key=lambda d: d["market_index"], reverse=True)
        return data[:limit]


city_service = CityService()
