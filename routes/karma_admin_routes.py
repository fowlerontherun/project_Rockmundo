from auth.dependencies import get_current_user_id, require_permission
from backend.karma_extras import add_karma_vote, get_karma_leaderboard, get_karma_score
from fastapi import APIRouter, Depends, HTTPException, Request

router = APIRouter(prefix="/karma", tags=["Karma"])


@router.get("/score/{user_id}", dependencies=[Depends(require_permission(["admin"]))])
def read_karma_score(
    user_id: int, _req: Request, _: int = Depends(get_current_user_id)
):
    return {"user_id": user_id, "karma": get_karma_score(user_id)}


@router.post("/vote")
def cast_vote(
    voter_id: int,
    target_id: int,
    vote: int,
    _req: Request,
    _: int = Depends(get_current_user_id),
):
    if vote not in (-1, 1):
        raise HTTPException(status_code=400, detail="vote must be -1 or 1")
    if voter_id == target_id:
        raise HTTPException(status_code=400, detail="self-vote not allowed")
    score = add_karma_vote(voter_id, target_id, vote)
    return {"target_id": target_id, "updated_karma": score}


@router.get("/leaderboard")
def karma_top(_req: Request, _: int = Depends(get_current_user_id)):
    return {"leaderboard": get_karma_leaderboard()}
