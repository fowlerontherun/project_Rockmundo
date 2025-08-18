# File: backend/routes/avatar.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from services.avatars_service import AvatarsService, AvatarError, AvatarIn

# Auth dependency (replace with your real one)
try:
    from auth.dependencies import require_role
except Exception:
    def require_role(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/avatars", tags=["Avatars"])
svc = AvatarsService()
svc.ensure_schema()

# -------- Models --------
class CreateAvatarIn(BaseModel):
    user_id: int
    display_name: Optional[str] = None
    body_type: Optional[str] = None
    face: Optional[str] = None
    hair: Optional[str] = None
    hair_color: Optional[str] = None
    eye_color: Optional[str] = None
    skin_tone: Optional[str] = None
    instrument: Optional[str] = None
    outfit_theme: Optional[str] = None
    pose: Optional[str] = None
    render_seed: Optional[str] = None

class UpdateAvatarIn(BaseModel):
    display_name: Optional[str] = None
    body_type: Optional[str] = None
    face: Optional[str] = None
    hair: Optional[str] = None
    hair_color: Optional[str] = None
    eye_color: Optional[str] = None
    skin_tone: Optional[str] = None
    instrument: Optional[str] = None
    outfit_theme: Optional[str] = None
    pose: Optional[str] = None
    render_seed: Optional[str] = None

class EquipIn(BaseModel):
    slot: str
    skin_id: int

class GrantIn(BaseModel):
    user_id: int
    skin_id: int
    qty: int = 1

# -------- Endpoints --------
@router.post("", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def create_avatar(payload: CreateAvatarIn):
    try:
        avatar_id = svc.create_avatar(AvatarIn(**payload.model_dump()))
        return {"id": avatar_id}
    except AvatarError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{avatar_id}", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def get_avatar(avatar_id: int):
    try:
        return svc.get_avatar(avatar_id)
    except AvatarError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def list_avatars(user_id: int | None = None):
    return svc.list_avatars(user_id=user_id)

@router.patch("/{avatar_id}", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def update_avatar(avatar_id: int, payload: UpdateAvatarIn):
    try:
        svc.update_avatar(avatar_id, {k:v for k,v in payload.model_dump().items() if v is not None})
        return {"ok": True}
    except AvatarError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{avatar_id}", dependencies=[Depends(require_role(["admin","moderator"]))])
def delete_avatar(avatar_id: int):
    try:
        svc.delete_avatar(avatar_id)
        return {"ok": True}
    except AvatarError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{avatar_id}/equip", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def equip_skin(avatar_id: int, payload: EquipIn):
    try:
        svc.equip_skin(avatar_id, payload.slot, payload.skin_id)
        return {"ok": True}
    except AvatarError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{avatar_id}/unequip", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def unequip_skin(avatar_id: int, slot: str):
    svc.unequip_skin(avatar_id, slot)
    return {"ok": True}

@router.get("/{avatar_id}/equipped", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def list_equipped(avatar_id: int):
    return svc.list_equipped(avatar_id)

@router.post("/inventory/grant", dependencies=[Depends(require_role(["admin","moderator"]))])
def grant_skin(payload: GrantIn):
    try:
        svc.grant_skin_to_user(payload.user_id, payload.skin_id, payload.qty)
        return {"ok": True}
    except AvatarError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/inventory/{user_id}", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def list_inventory(user_id: int):
    return svc.list_inventory(user_id)
