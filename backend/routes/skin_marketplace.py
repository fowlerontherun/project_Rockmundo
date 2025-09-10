from fastapi import APIRouter, HTTPException
from uuid import uuid4
from base64 import b64decode

from schemas.skin import SkinResponse, SkinCreate
from schemas.skin_marketplace import (
    SkinApplyRequest,
    SkinPurchaseRequest,
    SkinUploadRequest,
)
from services.skin_service import SkinService
from services.storage_service import get_storage_backend
from services.payment_service import PaymentError, PaymentService, MockGateway
from services.economy_service import EconomyService

router = APIRouter(prefix="/skins", tags=["Skins"])
svc = SkinService()
_economy = EconomyService()
_economy.ensure_schema()
_gateway = MockGateway(prefix="skin")
payments = PaymentService(_gateway, _economy)


@router.get("/", response_model=list[SkinResponse])
def list_skins():
    return svc.list_skins()


@router.post("/upload", response_model=SkinResponse)
def upload_skin(payload: SkinUploadRequest):
    """Upload a new skin using base64-encoded mesh and texture data."""

    storage = get_storage_backend()
    mesh_bytes = b64decode(payload.mesh_b64)
    tex_bytes = b64decode(payload.texture_b64)
    mesh_obj = storage.upload_bytes(
        mesh_bytes,
        f"skins/{uuid4()}-mesh.bin",
    )
    tex_obj = storage.upload_bytes(
        tex_bytes,
        f"skins/{uuid4()}-tex.bin",
    )
    skin = svc.create_skin(
        SkinCreate(
            name=payload.name,
            category=payload.category,
            mesh_url=mesh_obj.url,
            texture_url=tex_obj.url,
            rarity=payload.rarity,
            author=payload.author,
            price=payload.price,
        )
    )
    return skin


@router.post("/{skin_id}/purchase")
def purchase_skin(skin_id: int, payload: SkinPurchaseRequest):
    skin = svc.get_skin(skin_id)
    if not skin:
        raise HTTPException(status_code=404, detail="Skin not found")
    try:
        pid = payments.purchase_item(payload.avatar_id, skin.price)
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))
    svc.purchase_skin(payload.avatar_id, skin_id)
    return {"status": "purchased", "payment_id": pid}


@router.post("/{skin_id}/apply")
def apply_skin(skin_id: int, payload: SkinApplyRequest):
    avatar = svc.apply_skin(payload.avatar_id, skin_id)
    if not avatar:
        raise HTTPException(status_code=400, detail="Skin not owned")
    return {"status": "applied", "avatar_id": avatar.id}
