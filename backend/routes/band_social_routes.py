from auth.dependencies import get_current_user_id, require_role
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/alliances/create")
async def create_alliance(data: dict):
    return {"message": "Alliance created", "data": data}

@router.post("/rivalries/declaration")
async def declare_rivalry(data: dict):
    return {"message": "Rivalry declared", "data": data}