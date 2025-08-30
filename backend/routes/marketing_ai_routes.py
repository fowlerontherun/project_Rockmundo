from fastapi import APIRouter

from services.marketing_ai_service import (
    accept_promotion_plan,
    generate_promotion_plan,
)

router = APIRouter()


@router.post("/marketing_ai/plan")
def recommend_plan(data: dict):
    """Generate a marketing campaign plan for the band."""
    band_id = int(data.get("band_id"))
    return generate_promotion_plan(band_id)


@router.post("/marketing_ai/plan/accept")
def accept_plan(plan: dict):
    """Accept a proposed plan and persist it as promotions."""
    return accept_promotion_plan(plan)
