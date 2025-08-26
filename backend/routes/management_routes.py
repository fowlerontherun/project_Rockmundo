from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter
from schemas.management_schema import ManagerCreate, ManagerResponse
from datetime import date
from typing import List

router = APIRouter()
managers = []
manager_id_counter = 1

@router.post("/managers/", response_model=ManagerResponse, dependencies=[Depends(require_role(["user", "band_member", "moderator", "admin"]))])
def hire_manager(manager: ManagerCreate):
    global manager_id_counter
    new_manager = manager.dict()
    new_manager.update({
        "id": manager_id_counter,
        "hire_date": date.today(),
        "active": True
    })
    managers.append(new_manager)
    manager_id_counter += 1
    return new_manager

@router.get("/managers/", response_model=List[ManagerResponse])
def list_managers():
    return managers