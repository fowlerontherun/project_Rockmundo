from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter
from services.tutorial_service import *

router = APIRouter()

@router.post("/tutorial/start", dependencies=[Depends(require_role(["admin"]))])
def start_tutorial(user_id: int):
    return start_user_tutorial(user_id)

@router.post("/tutorial/complete_step")
def complete_tutorial_step(user_id: int, step: str):
    return mark_step_complete(user_id, step)

@router.get("/tutorial/tip")
def get_tip(stage: str):
    return get_contextual_tip(stage)