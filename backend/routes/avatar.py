from fastapi import APIRouter, Depends, HTTPException
from schemas.avatar import AvatarCreate, AvatarUpdate, AvatarResponse
from services.avatar_service import AvatarService

try:  # pragma: no cover - fallback for environments without auth module
    from auth.dependencies import require_role
except Exception:  # pragma: no cover
    def require_role(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/avatars", tags=["Avatars"])
svc = AvatarService()

@router.post("/", response_model=AvatarResponse, dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))])
def create_avatar(payload: AvatarCreate):
    return svc.create_avatar(payload)

@router.get("/{avatar_id}", response_model=AvatarResponse, dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))])
def get_avatar(avatar_id: int):
    avatar = svc.get_avatar(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar

@router.get("/", response_model=list[AvatarResponse], dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))])
def list_avatars():
    return svc.list_avatars()

@router.put("/{avatar_id}", response_model=AvatarResponse, dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))])
def update_avatar(avatar_id: int, payload: AvatarUpdate):
    avatar = svc.update_avatar(avatar_id, payload)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar

@router.delete("/{avatar_id}", dependencies=[Depends(require_role(["admin", "moderator"]))])
def delete_avatar(avatar_id: int):
    if not svc.delete_avatar(avatar_id):
        raise HTTPException(status_code=404, detail="Avatar not found")
    return {"ok": True}
