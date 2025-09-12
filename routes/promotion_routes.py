from backend.auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter
from schemas.promotion_schema import PromotionCreate, PromotionResponse
from typing import List

router = APIRouter()
promotions_db = []
promotion_id_counter = 1

@router.post("/promotions/", response_model=PromotionResponse, dependencies=[Depends(require_permission(["admin", "moderator", "band_member"]))])
def create_promotion(promo: PromotionCreate):
    global promotion_id_counter
    new_promo = promo.dict()
    new_promo.update({
        "id": promotion_id_counter,
        "outcome": "neutral",
        "fame_change": 0.0,
        "fan_gain": 0,
        "press_score_change": 0.0,
        "controversy_level": 0.0
    })
    promotions_db.append(new_promo)
    promotion_id_counter += 1
    return new_promo

@router.get("/promotions/", response_model=List[PromotionResponse])
def list_promotions():
    return promotions_db