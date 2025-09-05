from auth.dependencies import get_current_user_id, require_permission
from fastapi import APIRouter, HTTPException
from models.fan_club_models import *
from schemas.fan_club_schemas import *

router = APIRouter()

@router.post("/fan_club/create", dependencies=[Depends(require_permission(["admin", "moderator", "band_member"]))])
def create_fan_club(fan_club: FanClubCreate):
    return {"message": f"Fan club '{fan_club.name}' created for band {fan_club.band_id}"}

@router.post("/fan_club/join")
def join_fan_club(join_request: FanClubJoin):
    return {"message": f"User {join_request.user_id} joined fan club {join_request.fan_club_id}"}

@router.get("/fan_club/top_fans/{fan_club_id}")
def get_top_fans(fan_club_id: int):
    return {"top_fans": ["Fan1", "Fan2", "Fan3"]}

@router.post("/fan_club/post_mission")
def post_mission(mission: FanMissionCreate):
    return {"message": f"Mission '{mission.title}' created for fan club {mission.fan_club_id}"}
