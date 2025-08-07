from fastapi import APIRouter
from core.ai_tour_scheduler import run_ai_scheduler, scheduled_tours

router = APIRouter()

@router.post("/ai_tour_scheduler/run")
def run_scheduler():
    results = run_ai_scheduler()
    return {"scheduled": results}

@router.get("/ai_tour_scheduler/history")
def get_schedule_history():
    return scheduled_tours