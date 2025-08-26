from auth.dependencies import get_current_user_id, require_role
# File: backend/routes/sales.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from services.sales_service import SalesService, SalesError

# Adjust to your project's auth dep path
try:
    from auth.dependencies import require_role
except Exception:
    def require_role(roles):
        async def _noop():
            return True
        return _noop

router = APIRouter(prefix="/sales", tags=["Sales"])

svc = SalesService()
svc.ensure_schema()

# -------- Digital --------
class DigitalSaleIn(BaseModel):
    
buyer_user_id: int
    work_type: str  # 'song' | 'album'
    work_id: int
    price_cents: int
    currency: str = "USD"
    source: str | None = "store"

@router.post("/digital", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def record_digital(payload: DigitalSaleIn):
    try:
        sid = svc.record_digital_sale(**payload.model_dump())
        return {"sale_id": sid}
    except SalesError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/digital/{work_type}/{work_id}", dependencies=[Depends(require_role(["admin","moderator"]))])
def list_digital_sales(work_type: str, work_id: int):
    return svc.list_digital_sales_for_work(work_type, work_id)

# -------- Vinyl --------
class VinylSkuIn(BaseModel):
    
album_id: int
    variant: str
    price_cents: int
    stock_qty: int
    currency: str = "USD"

class VinylItemIn(BaseModel):
    
sku_id: int
    qty: int

class VinylPurchaseIn(BaseModel):
    
buyer_user_id: int
    items: List[VinylItemIn]
    shipping_address: str | None = None

@router.post("/vinyl/sku", dependencies=[Depends(require_role(["admin","moderator"]))])
def create_vinyl_sku(payload: VinylSkuIn):
    try:
        sku_id = svc.create_vinyl_sku(**payload.model_dump())
        return {"sku_id": sku_id}
    except SalesError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/vinyl/sku/{album_id}", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def list_vinyl_skus(album_id: int):
    return svc.list_vinyl_skus(album_id)

@router.post("/vinyl/purchase", dependencies=[Depends(require_role(["band_member","admin","moderator"]))])
def purchase_vinyl(payload: VinylPurchaseIn):
    try:
        order_id = svc.purchase_vinyl(
            buyer_user_id=payload.buyer_user_id,
            items=[i.model_dump() for i in payload.items],
            shipping_address=payload.shipping_address,
        )
        return {"order_id": order_id}
    except SalesError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/vinyl/refund/{order_id}", dependencies=[Depends(require_role(["admin","moderator"]))])
def refund_vinyl(order_id: int, reason: str = ""):
    try:
        return svc.refund_vinyl_order(order_id, reason)
    except SalesError as e:
        raise HTTPException(status_code=400, detail=str(e))
