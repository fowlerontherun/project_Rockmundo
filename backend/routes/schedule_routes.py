from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.activity_processor import evaluate_schedule_completion
from backend.services.plan_service import plan_service
from backend.services.schedule_service import schedule_service

router = APIRouter(prefix="/schedule", tags=["schedule"])


class PlanSelections(BaseModel):
    social: bool = False
    career: bool = False
    band: bool = False


class RecommendationRequest(BaseModel):
    user_id: int
    goals: List[str]


@router.post("/plan")
def generate_plan(data: PlanSelections):
    schedule = plan_service.create_plan(
        social=data.social, career=data.career, band=data.band
    )
    return {"schedule": schedule}


@router.post("/recommend")
def recommend_activities(data: RecommendationRequest):
    suggestions = plan_service.recommend_activities(data.user_id, data.goals)
    return {"recommendations": suggestions}


class DefaultEntry(BaseModel):
    hour: int
    activity_id: int


@router.post("/default-plan/{user_id}/{day}")
def set_default_plan(user_id: int, day: str, entries: List[DefaultEntry]):
    schedule_service.set_default_plan(user_id, day, [e.dict() for e in entries])
    return {"status": "ok"}


@router.get("/default-plan/{user_id}/{day}")
def get_default_plan(user_id: int, day: str):
    plan = schedule_service.get_default_plan(user_id, day)
    return {"plan": plan}


class WeeklyEntry(BaseModel):
    day: str
    slot: int
    activity_id: int


@router.post("/weekly/{user_id}/{week_start}")
def set_weekly_schedule(user_id: int, week_start: str, entries: List[WeeklyEntry]):
    schedule_service.set_weekly_schedule(user_id, week_start, [e.dict() for e in entries])
    return {"status": "ok"}


@router.get("/weekly/{user_id}/{week_start}")
def get_weekly_schedule(user_id: int, week_start: str):
    schedule = schedule_service.get_weekly_schedule(user_id, week_start)
    return {"schedule": schedule}


class DailyEntry(BaseModel):
    slot: int
    activity_id: int
    auto_split: bool = False


@router.post("/daily/{user_id}/{date}")
def schedule_daily_activity(user_id: int, date: str, entry: DailyEntry):
    try:
        conflicts = schedule_service.schedule_activity(
            user_id,
            date,
            entry.slot,
            entry.activity_id,
            auto_split=entry.auto_split,
        )
    except ValueError as exc:
        return {"status": "conflict", "conflicts": getattr(exc, "conflicts", [])}

    if entry.auto_split and conflicts:
        return {"status": "partial", "conflicts": conflicts}

    return {"status": "ok"}


@router.get("/stats/{user_id}/{date}")
def get_schedule_stats(user_id: int, date: str):
    return evaluate_schedule_completion(user_id, date)


@router.get("/history/{date}")
def get_schedule_history(date: str):
    history = schedule_service.get_schedule_history(date)
    return {"history": history}
