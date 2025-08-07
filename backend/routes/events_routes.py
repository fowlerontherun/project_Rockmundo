from fastapi import APIRouter
from services.events_service import *

router = APIRouter()

@router.post("/events/create")
def create_event(payload: dict):
    return create_seasonal_event(payload)

@router.post("/events/end")
def end_event(payload: dict):
    return end_seasonal_event(payload["event_id"])

@router.get("/events/current")
def get_current_event():
    return get_active_event()

@router.get("/events/history")
def get_event_history():
    return get_past_events()