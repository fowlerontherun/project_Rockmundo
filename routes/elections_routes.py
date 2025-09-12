from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Depends
from services.election_service import *

router = APIRouter()

@router.post("/elections/candidate")
def declare_candidacy(payload: dict):
    return declare_candidate(payload)

@router.post("/elections/vote")
def cast_vote(payload: dict):
    return vote_for_candidate(payload)

@router.get("/elections/results")
def get_results():
    return get_election_results()