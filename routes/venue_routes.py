from backend.auth.dependencies import get_current_user_id, require_permission
# File: backend/routes/venue_routes.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from services.tour_service import TourService

router = APIRouter(prefix="/venues", tags=["Venues"])
svc = TourService()

class CreateVenueIn(BaseModel):
    
name: str
    city: Optional[str] = ""
    country: Optional[str] = ""
    capacity: int = Field(0, ge=0)

@router.post("/")
def create_venue(payload: CreateVenueIn):
    return svc.create_venue(name=payload.name, city=payload.city or "", country=payload.country or "", capacity=payload.capacity)

@router.get("/")
def list_venues(q: Optional[str] = None, limit: int = 50, offset: int = 0):
    return svc.list_venues(q=q, limit=limit, offset=offset)

@router.get("/{venue_id}/availability")
def venue_availability(venue_id: int, start: str, end: str):
    return svc.venue_availability(venue_id=venue_id, start=start, end=end)
