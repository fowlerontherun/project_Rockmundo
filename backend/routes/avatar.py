from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from schemas.avatar import AvatarCreate, AvatarResponse, AvatarUpdate
from services.avatar_service import AvatarService
from services.lifestyle_service import calculate_lifestyle_score, evaluate_lifestyle_risks

try:  # pragma: no cover - fallback for environments without auth module
    from auth.dependencies import require_permission
except Exception:  # pragma: no cover
    def require_permission(roles):
        async def _noop():
            return True

        return _noop

router = APIRouter(prefix="/avatars", tags=["Avatars"])
svc = AvatarService()


class LifestylePayload(BaseModel):
    """Minimal lifestyle data used to influence mood."""

    sleep_hours: float
    stress: int
    training_discipline: int
    mental_health: int
    drinking: str = "none"
    nutrition: int = 70
    fitness: int = 70

@router.post("/", response_model=AvatarResponse, dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))])
def create_avatar(payload: AvatarCreate):
    return svc.create_avatar(payload)

@router.get("/{avatar_id}", response_model=AvatarResponse, dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))])
def get_avatar(avatar_id: int):
    avatar = svc.get_avatar(avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar

@router.get("/", response_model=list[AvatarResponse], dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))])
def list_avatars():
    return svc.list_avatars()

@router.put("/{avatar_id}", response_model=AvatarResponse, dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))])
def update_avatar(avatar_id: int, payload: AvatarUpdate):
    avatar = svc.update_avatar(avatar_id, payload)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar

@router.delete("/{avatar_id}", dependencies=[Depends(require_permission(["admin", "moderator"]))])
def delete_avatar(avatar_id: int):
    if not svc.delete_avatar(avatar_id):
        raise HTTPException(status_code=404, detail="Avatar not found")
    return {"ok": True}


@router.get(
    "/{avatar_id}/mood",
    dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))],
)
def get_mood(avatar_id: int):
    mood = svc.get_mood(avatar_id)
    if mood is None:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return {"mood": mood}


@router.post(
    "/{avatar_id}/mood",
    response_model=AvatarResponse,
    dependencies=[Depends(require_permission(["band_member", "admin", "moderator"]))],
)
def influence_mood(avatar_id: int, payload: LifestylePayload):
    data = payload.model_dump()
    score = calculate_lifestyle_score(data)
    events = evaluate_lifestyle_risks(data)
    avatar = svc.adjust_mood(avatar_id, score, events)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return avatar
