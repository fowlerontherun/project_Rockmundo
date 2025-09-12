from backend.auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter
from core.ai_tour_scheduler import run_ai_scheduler, scheduled_tours

router = APIRouter()

@router.post("/ai_tour_scheduler/run", dependencies=[Depends(require_permission(["user", "band_member", "moderator", "admin"]))])
def run_scheduler():
    results = run_ai_scheduler()
    return {"scheduled": results}

@router.get("/ai_tour_scheduler/history")
def get_schedule_history():
    return scheduled_tours