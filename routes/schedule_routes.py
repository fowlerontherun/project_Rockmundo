from typing import List

from fastapi import APIRouter, Response
from pydantic import BaseModel

from services.analytics_service import schedule_analytics_service
from services.calendar_export import daily_schedule_to_ics
from services.plan_service import plan_service
from services.schedule_service import schedule_service

router = APIRouter(prefix="/schedule", tags=["schedule"])


class PlanPercentages(BaseModel):
    social_pct: int = 0
    career_pct: int = 0
    band_pct: int = 0


class RecommendationRequest(BaseModel):
    user_id: int
    goals: List[str]


@router.post("/plan")
def generate_plan(data: PlanPercentages):
    schedule = plan_service.create_plan(
        social_pct=data.social_pct,
        career_pct=data.career_pct,
        band_pct=data.band_pct,
    )
    return {"schedule": schedule}


@router.post("/recommend")
def recommend_activities(data: RecommendationRequest):
    suggestions = plan_service.recommend_activities(data.user_id, data.goals)
    return {"recommendations": suggestions}


class SimulationEntry(BaseModel):
    activity_id: int


class PlanSimulation(BaseModel):
    user_id: int
    entries: List[SimulationEntry]


@router.post("/simulate")
def simulate_schedule(data: PlanSimulation):
    from services.activity_processor import simulate_plan

    return simulate_plan(data.user_id, [e.model_dump() for e in data.entries])


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


@router.get("/analytics/{user_id}/{week_start}")
def get_schedule_analytics(user_id: int, week_start: str):
    data = schedule_analytics_service.weekly_totals(user_id, week_start)
    return data


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
    from services.activity_processor import evaluate_schedule_completion

    return evaluate_schedule_completion(user_id, date)


@router.get("/history/{date}")
def get_schedule_history(date: str):
    history = schedule_service.get_schedule_history(date)
    return {"history": history}


@router.get("/export/ics")
def export_schedule_ics(user_id: int, date: str):
    ics = daily_schedule_to_ics(user_id, date)
    return Response(
        content=ics,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="schedule.ics"'},
    )


class TemplateEntry(BaseModel):
    hour: int
    activity_id: int


class TemplateCreate(BaseModel):
    name: str
    entries: List[TemplateEntry]


class CopyRequest(BaseModel):
    user_id: int
    src_date: str
    dest_dates: List[str]


@router.post("/templates/{user_id}")
def create_template(user_id: int, data: TemplateCreate):
    template_id = schedule_service.create_template(
        user_id, data.name, [e.dict() for e in data.entries]
    )
    return {"id": template_id}


@router.get("/templates/{user_id}")
def list_templates(user_id: int):
    templates = schedule_service.list_templates(user_id)
    return {"templates": templates}


@router.post("/apply-template/{user_id}/{date}/{template_id}")
def apply_template(user_id: int, date: str, template_id: int):
    schedule_service.apply_template(user_id, date, template_id)
    return {"status": "ok"}


@router.post("/copy")
def copy_schedule(data: CopyRequest):
    schedule_service.copy_schedule(data.user_id, data.src_date, data.dest_dates)
    return {"status": "ok"}
