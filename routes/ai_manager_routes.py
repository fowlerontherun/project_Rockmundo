from backend.auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, Depends
from services.ai_manager_service import *

router = APIRouter()

@router.post("/ai_manager/activate")
def activate_ai(ai_profile: dict):
    return activate_ai_manager(ai_profile)

@router.get("/ai_manager/suggestions/{band_id}")
def get_ai_suggestions(band_id: int):
    return get_band_suggestions(band_id)

@router.post("/ai_manager/override")
def override_ai(data: dict):
    return override_ai_manager(data)