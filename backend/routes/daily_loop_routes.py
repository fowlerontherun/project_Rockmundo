from fastapi import APIRouter
from pydantic import BaseModel

from backend.models import daily_loop

router = APIRouter(prefix="/daily", tags=["DailyLoop"])


@router.get("/status/{user_id}")
def get_status(user_id: int):
    return daily_loop.get_status(user_id)


class ClaimRequest(BaseModel):
    user_id: int


@router.post("/claim")
def claim_reward(req: ClaimRequest):
    return daily_loop.claim_reward(req.user_id)
