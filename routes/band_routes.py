from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import band_service
from services.avatar_service import AvatarService
from schemas.avatar import AvatarUpdate

router = APIRouter(prefix="/bands", tags=["Bands"])

_avatar_service = AvatarService()


class LeadershipUpdate(BaseModel):
    leadership: int


@router.get("/{band_id}/leadership")
def get_band_leadership(band_id: int):
    info = band_service.get_band_info(band_id)
    if not info:
        raise HTTPException(status_code=404, detail="Band not found")
    data = []
    for member in info["members"]:
        avatar = _avatar_service.get_avatar_by_character_id(member["user_id"])
        data.append(
            {
                "user_id": member["user_id"],
                "leadership": avatar.leadership if avatar else None,
            }
        )
    return data


@router.put("/{band_id}/leadership/{user_id}")
def update_leadership(band_id: int, user_id: int, payload: LeadershipUpdate):
    info = band_service.get_band_info(band_id)
    if not info or user_id not in [m["user_id"] for m in info["members"]]:
        raise HTTPException(status_code=404, detail="Member not found")
    avatar = _avatar_service.get_avatar_by_character_id(user_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    _avatar_service.update_avatar(avatar.id, AvatarUpdate(leadership=payload.leadership))
    updated = _avatar_service.get_avatar(avatar.id)
    return {"user_id": user_id, "leadership": updated.leadership}
