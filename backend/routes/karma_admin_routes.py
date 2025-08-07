from fastapi import APIRouter
from karma_extras import get_karma_score, get_karma_leaderboard, add_karma_vote

router = APIRouter()

@router.get("/karma/score/{user_id}")
def read_karma_score(user_id: int):
    return {"user_id": user_id, "karma": get_karma_score(user_id)}

@router.post("/karma/vote")
def cast_vote(voter_id: int, target_id: int, vote: int):
    score = add_karma_vote(voter_id, target_id, vote)
    return {"target_id": target_id, "updated_karma": score}

@router.get("/karma/leaderboard")
def karma_top():
    return {"leaderboard": get_karma_leaderboard()}