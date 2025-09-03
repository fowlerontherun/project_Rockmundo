from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.plan_service import plan_service

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
