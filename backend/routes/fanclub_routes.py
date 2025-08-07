from fastapi import APIRouter
from schemas.fanclub_schema import FanClubCreate, FanClubResponse
from datetime import date
from typing import List

router = APIRouter()
fanclubs = []
fanclub_id_counter = 1

@router.post("/fanclubs/", response_model=FanClubResponse)
def create_fanclub(fanclub: FanClubCreate):
    global fanclub_id_counter
    new_fc = fanclub.dict()
    new_fc.update({
        "id": fanclub_id_counter,
        "creation_date": date.today(),
        "membership_tiers": { "casual": 0, "active": 0, "loyal": 0, "superfan": 0 },
        "superfan_ids": [],
        "exclusive_content_ids": [],
    })
    fanclubs.append(new_fc)
    fanclub_id_counter += 1
    return new_fc

@router.get("/fanclubs/", response_model=List[FanClubResponse])
def list_fanclubs():
    return fanclubs