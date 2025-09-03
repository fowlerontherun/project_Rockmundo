from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.plan_service import plan_service
from backend.services.schedule_service import schedule_service

router = APIRouter(prefix="/schedule", tags=["schedule"])


class PlanSelections(BaseModel):
    social: bool = False
    career: bool = False
    band: bool = False


@router.post("/plan")
def generate_plan(data: PlanSelections):
    schedule = plan_service.create_plan(
        social=data.social, career=data.career, band=data.band
    )
    return {"schedule": schedule}


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
