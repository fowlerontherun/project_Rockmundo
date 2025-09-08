from fastapi import APIRouter, Depends, HTTPException
from schemas.avatar import AvatarResponse
from services.avatar_service import AvatarService

try:  # pragma: no cover - fallback when auth module absent
    from auth.dependencies import require_permission
except Exception:  # pragma: no cover
    def require_permission(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/avatars", tags=["Avatars"])
svc = AvatarService()


@router.post(
    "/{avatar_id}/rest",
    response_model=AvatarResponse,
    dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))],
)
def rest_avatar(avatar_id: int):
    avatar = svc.rest(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar
