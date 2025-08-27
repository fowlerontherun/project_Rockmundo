# File: backend/routes/tour_routes.py
from fastapi import APIRouter, HTTPException, Query
from fastapi import Depends
from auth.dependencies import get_current_user_id, require_role
from pydantic import BaseModel, Field
from typing import Optional, List

from services.tour_service import TourService, TourError
from services.achievement_service import AchievementService

router = APIRouter(prefix="/tours", tags=["Tours"])
_achievements = AchievementService()
svc = TourService(achievements=_achievements)

# ---- Models ----
class CreateTourIn(BaseModel):
    
band_id: int = Field(..., ge=1)
    name: str

class AddStopIn(BaseModel):
    
tour_id: int = Field(..., ge=1)
    venue_id: int = Field(..., ge=1)
    date_start: str  # ISO format
    date_end: str
    order_index: int = 0
    notes: Optional[str] = ""

class UpdateStopStatusIn(BaseModel):
    
stop_id: int = Field(..., ge=1)
    status: str

# ---- Routes ----
@router.post("/")
def create_tour(payload: CreateTourIn, user_id: int = Depends(get_current_user_id)):
    return svc.create_tour(band_id=payload.band_id, name=payload.name)

@router.get("/")
def list_tours(band_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0, user_id: int = Depends(get_current_user_id)):
    return svc.list_tours(band_id=band_id, status=status, limit=limit, offset=offset)

@router.get("/{tour_id}")
def get_tour(tour_id: int, user_id: int = Depends(get_current_user_id)):
    try:
        return svc.get_tour(tour_id)
    except TourError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/confirm/{tour_id}")
def confirm_tour(tour_id: int, user_id: int = Depends(get_current_user_id)):
    try:
        return svc.confirm_tour(tour_id)
    except TourError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stops")
def add_stop(payload: AddStopIn, user_id: int = Depends(get_current_user_id)):
    try:
        return svc.add_stop(
            tour_id=payload.tour_id,
            venue_id=payload.venue_id,
            date_start=payload.date_start,
            date_end=payload.date_end,
            order_index=payload.order_index,
            notes=payload.notes or ""
        )
    except TourError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{tour_id}/stops")
def list_stops(tour_id: int, user_id: int = Depends(get_current_user_id)):
    return svc.list_stops(tour_id)

@router.post("/stops/status")
def update_stop_status(payload: UpdateStopStatusIn, user_id: int = Depends(get_current_user_id)):
    try:
        return svc.update_stop_status(stop_id=payload.stop_id, status=payload.status)
    except TourError as e:
        raise HTTPException(status_code=400, detail=str(e))