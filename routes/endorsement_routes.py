from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter
from schemas.endorsement_schema import EndorsementCreate, EndorsementResponse
from datetime import date
from typing import List

router = APIRouter()
endorsements = []
endorsement_id_counter = 1

@router.post("/endorsements/", response_model=EndorsementResponse, dependencies=[Depends(require_permission(["admin"]))])
def create_endorsement(endorsement: EndorsementCreate):
    global endorsement_id_counter
    new_endorsement = endorsement.dict()
    new_endorsement.update({
        "id": endorsement_id_counter,
        "start_date": date.today(),
        "active": True
    })
    endorsements.append(new_endorsement)
    endorsement_id_counter += 1
    return new_endorsement

@router.get("/endorsements/", response_model=List[EndorsementResponse])
def list_endorsements():
    return endorsements