"""Routes for tour planning and itinerary optimization."""

from __future__ import annotations

import math
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.fame_service import FameService
from services.tour_service import (
    RECORDING_FAME_THRESHOLD,
    MAX_RECORDINGS_PER_YEAR,
    TourService,
)

router = APIRouter(prefix="/tour-planner", tags=["TourPlanner"])
svc = TourService()


class _FameDB:
    def get_band_fame_total(self, band_id: int) -> int:
        return 0


fame_service = FameService(_FameDB())


class TourRequest(BaseModel):
    """Incoming payload for tour planning."""

    route: List[str]
    vehicle_type: str
    band_id: int
    record_stops: List[int] = []


class TourResponse(BaseModel):
    """Response containing an optimized itinerary and costs."""

    itinerary: List[str]
    total_distance: float
    total_time: float
    total_cost: float
    record_stops: List[int] = []


class RecordingUpdate(BaseModel):
    stop_id: int
    is_recorded: bool


class ScheduleUpdateRequest(BaseModel):
    updates: List[RecordingUpdate]


# Simple city database with lat/long coordinates
CITY_COORDS = {
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298),
    "Houston": (29.7604, -95.3698),
    "Phoenix": (33.4484, -112.0740),
}


VEHICLE_SPEEDS_KMH = {
    "van": 80.0,
    "bus": 70.0,
    "truck": 65.0,
    "plane": 800.0,
}


COST_PER_KM = {
    "van": 0.5,
    "bus": 0.7,
    "truck": 0.9,
    "plane": 5.0,
}


def haversine(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
    """Return distance in km between two (lat, lon) pairs using Haversine formula."""

    lat1, lon1 = coord1
    lat2, lon2 = coord2
    radius = 6371.0

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.post("/optimize", response_model=TourResponse)
def optimize_tour(payload: TourRequest) -> TourResponse:
    """Calculate travel distance, time and cost and reorder route greedily."""

    if len(payload.route) < 2:
        raise HTTPException(status_code=400, detail="At least two cities required")

    for city in payload.route:
        if city not in CITY_COORDS:
            raise HTTPException(status_code=400, detail=f"Unknown city: {city}")

    if payload.record_stops:
        fame = fame_service.get_total_fame(payload.band_id)
        if fame < RECORDING_FAME_THRESHOLD:
            raise HTTPException(status_code=403, detail="Not enough fame to record stops")
        current = svc.get_band_recorded_count(payload.band_id)
        if current + len(payload.record_stops) > MAX_RECORDINGS_PER_YEAR:
            raise HTTPException(status_code=400, detail="Recording limit exceeded")
        if any(i < 0 or i >= len(payload.route) for i in payload.record_stops):
            raise HTTPException(status_code=400, detail="Invalid recording index")

    remaining = payload.route[:]
    itinerary = [remaining.pop(0)]
    while remaining:
        last = itinerary[-1]
        next_city = min(
            remaining,
            key=lambda c: haversine(CITY_COORDS[last], CITY_COORDS[c]),
        )
        itinerary.append(next_city)
        remaining.remove(next_city)

    vehicle_key = payload.vehicle_type.lower()
    speed = VEHICLE_SPEEDS_KMH.get(vehicle_key)
    cost_km = COST_PER_KM.get(vehicle_key)
    if speed is None or cost_km is None:
        raise HTTPException(status_code=400, detail="Unknown vehicle type")

    total_distance = 0.0
    for i in range(len(itinerary) - 1):
        total_distance += haversine(
            CITY_COORDS[itinerary[i]], CITY_COORDS[itinerary[i + 1]]
        )

    total_time = total_distance / speed
    total_cost = total_distance * cost_km

    return TourResponse(
        itinerary=itinerary,
        total_distance=total_distance,
        total_time=total_time,
        total_cost=total_cost,
        record_stops=payload.record_stops,
    )


@router.post("/schedule/update")
def update_schedule(payload: ScheduleUpdateRequest):
    """Persist recording selections for existing tour stops."""

    updated = [svc.update_stop_recording(u.stop_id, u.is_recorded) for u in payload.updates]
    return {"stops": updated}

