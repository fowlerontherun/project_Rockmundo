from fastapi import APIRouter, Depends, HTTPException
from auth.character_dependencies import get_current_character_id
from pydantic import BaseModel

from backend.models import daily_loop

router = APIRouter(prefix="/daily", tags=["DailyLoop"])

@router.get("/status/{user_id}")
def get_status(user_id: int, character_id: int = Depends(get_current_character_id)):
    if user_id != character_id:
        raise HTTPException(status_code=403, detail="Daily progress belongs to the selected character")
    return daily_loop.get_status(character_id)


class ClaimRequest(BaseModel):
    user_id: int


@router.post("/claim")
def claim_reward(req: ClaimRequest, character_id: int = Depends(get_current_character_id)):
    if req.user_id != character_id:
        raise HTTPException(status_code=403, detail="Daily progress belongs to the selected character")
    return daily_loop.claim_reward(character_id)


class TokenGrantRequest(BaseModel):
    user_id: int
    amount: int = 1


@router.post("/grant-token")
def grant_token(req: TokenGrantRequest, character_id: int = Depends(get_current_character_id)):
    if req.user_id != character_id:
        raise HTTPException(status_code=403, detail="Daily progress belongs to the selected character")
    return daily_loop.grant_catch_up_tokens(character_id, req.amount)


@router.post("/rotate")
def rotate_challenge():
    daily_loop.rotate_daily_challenge()
    return {"status": "ok"}
