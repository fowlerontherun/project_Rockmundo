from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter
from core.ai_transport_optimizer import optimize_transport_for_tour, get_transport_bookings

router = APIRouter()

@router.post("/ai_transport/optimize", dependencies=[Depends(require_role(["user", "band_member", "moderator", "admin"]))])
def optimize_transport(band_id: int, gear_weight: float, crew_size: int, budget: float):
    result = optimize_transport_for_tour(band_id, gear_weight, crew_size, budget)
    if result:
        return {"status": "success", "booking": result}
    return {"status": "failed", "reason": "No suitable transport found."}

@router.get("/ai_transport/bookings")
def list_bookings():
    return get_transport_bookings()