from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter
from services.skins_service import *

router = APIRouter()

@router.post("/skins/submit", dependencies=[Depends(require_permission(["admin", "moderator", "band_member"]))])
def submit_skin(payload: dict):
    return submit_new_skin(payload)

@router.get("/skins/pending")
def list_pending_skins():
    return get_pending_skins()

@router.post("/skins/vote")
def vote_skin(payload: dict):
    return vote_on_skin(payload)

@router.post("/skins/purchase")
def purchase_skin(payload: dict):
    return purchase_user_skin(payload)