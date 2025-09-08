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


class TokenGrantRequest(BaseModel):
    user_id: int
    amount: int = 1


@router.post("/grant-token")
def grant_token(req: TokenGrantRequest):
    return daily_loop.grant_catch_up_tokens(req.user_id, req.amount)


@router.post("/rotate")
def rotate_challenge():
    daily_loop.rotate_daily_challenge()
    return {"status": "ok"}
