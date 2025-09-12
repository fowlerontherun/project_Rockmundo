from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter
from schemas.merchandise_schema import MerchandiseCreate, MerchandiseResponse
from typing import List

router = APIRouter()
merch_db = []
merch_id_counter = 1

@router.post("/merchandise/", response_model=MerchandiseResponse, dependencies=[Depends(require_permission(["admin", "moderator", "band_member"]))])
def create_merch(merch: MerchandiseCreate):
    global merch_id_counter
    new_merch = merch.dict()
    new_merch.update({
        "id": merch_id_counter,
        "quantity_sold": 0,
        "fame_boost_on_sale": 0.0,
    })
    merch_db.append(new_merch)
    merch_id_counter += 1
    return new_merch

@router.get("/merchandise/", response_model=List[MerchandiseResponse])
def list_merchandise():
    return merch_db