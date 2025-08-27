from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.services.mod_marketplace_service import ModMarketplaceService

router = APIRouter(prefix="/modding", tags=["modding"])
service = ModMarketplaceService()


@router.post("/mods")
async def publish_mod(
    author_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    price_cents: int = Form(0),
    file: UploadFile = File(...),
):
    data = await file.read()
    mod_id = service.publish_mod(author_id, name, description, price_cents, data, file.content_type or "application/octet-stream")
    return {"id": mod_id}


@router.post("/mods/{mod_id}/rate")
def rate_mod(mod_id: int, user_id: int, rating: int):
    try:
        service.rate_mod(user_id, mod_id, rating)
    except Exception as e:  # pragma: no cover - safety net
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}


@router.post("/mods/{mod_id}/download")
def download_mod(mod_id: int, user_id: int):
    try:
        url = service.download_mod(user_id, mod_id)
    except Exception as e:  # pragma: no cover - safety net
        raise HTTPException(status_code=400, detail=str(e))
    return {"url": url}


# ----------- admin review routes -----------
@router.get("/admin/mods/pending")
def pending_mods():
    return service.list_pending_mods()


@router.post("/admin/mods/{mod_id}/approve")
def approve_mod(mod_id: int):
    try:
        service.approve_mod(mod_id)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}
