from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class TicketTier:
    """Represents a tier of tickets for a show."""
    name: str
    price: float
    capacity: int
    sold: int = 0

    def to_dict(self) -> dict:
        return self.__dict__


@dataclass
class Expense:
    description: str
    amount: float

    def to_dict(self) -> dict:
        return self.__dict__


@dataclass
class TourLeg:
    city: str
    venue: str
    date: str
    ticket_tiers: List[TicketTier] = field(default_factory=list)
    expenses: List[Expense] = field(default_factory=list)
    travel_distance: float = 0.0
    travel_hours: float = 0.0
    attendance: int = 0
    revenue: float = 0.0
    profit: float = 0.0
    status: str = "scheduled"
    is_recorded: bool = False

    def to_dict(self) -> dict:
        return {
            "city": self.city,
            "venue": self.venue,
            "date": self.date,
            "ticket_tiers": [t.to_dict() for t in self.ticket_tiers],
            "expenses": [e.to_dict() for e in self.expenses],
            "travel_distance": self.travel_distance,
            "travel_hours": self.travel_hours,
            "attendance": self.attendance,
            "revenue": self.revenue,
            "profit": self.profit,
            "status": self.status,
            "is_recorded": self.is_recorded,
        }


@dataclass
class Tour:
    id: int
    band_id: int
    title: str
    start_date: str
    end_date: str
    route: List[str]
    vehicle_type: str
    status: str = "planned"
    legs: List[TourLeg] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "band_id": self.band_id,
            "title": self.title,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "route": self.route,
            "vehicle_type": self.vehicle_type,
            "status": self.status,
            "legs": [leg.to_dict() for leg in self.legs],
            "created_at": self.created_at,
        }
