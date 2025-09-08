from fastapi import APIRouter, HTTPException

from schemas.skin import SkinResponse
from schemas.skin_marketplace import SkinApplyRequest, SkinPurchaseRequest
from services.skin_service import SkinService

router = APIRouter(prefix="/skins", tags=["Skins"])
svc = SkinService()


@router.get("/", response_model=list[SkinResponse])
def list_skins():
    return svc.list_skins()


@router.post("/{skin_id}/purchase")
def purchase_skin(skin_id: int, payload: SkinPurchaseRequest):
    svc.purchase_skin(payload.avatar_id, skin_id)
    return {"status": "purchased"}


@router.post("/{skin_id}/apply")
def apply_skin(skin_id: int, payload: SkinApplyRequest):
    avatar = svc.apply_skin(payload.avatar_id, skin_id)
    if not avatar:
        raise HTTPException(status_code=400, detail="Skin not owned")
    return {"status": "applied", "avatar_id": avatar.id}
