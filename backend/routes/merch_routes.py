from typing import List

from backend.auth.dependencies import get_current_user_id, require_role  # noqa: F401
from backend.services.economy_service import EconomyService
from backend.services.merch_service import MerchError, MerchService
from backend.models.merch import ProductIn, SKUIn
from fastapi import APIRouter, Depends, HTTPException, Request  # noqa: F401
from pydantic import BaseModel

router = APIRouter(prefix="/merch", tags=["Merch Store"])
svc = MerchService(economy=EconomyService())
svc.ensure_schema()


class ProductCreateIn(BaseModel):
    name: str
    category: str
    band_id: int | None = None
    description: str | None = None
    image_url: str | None = None
    is_active: bool = True


class SKUCreateIn(BaseModel):
    product_id: int
    price_cents: int
    stock_qty: int
    option_size: str | None = None
    option_color: str | None = None
    currency: str = "USD"
    barcode: str | None = None
    is_active: bool = True


class PurchaseItemIn(BaseModel):
    sku_id: int
    qty: int


class PurchaseIn(BaseModel):
    buyer_user_id: int
    items: List[PurchaseItemIn]
    shipping_address: str | None = None


@router.post("/products", dependencies=[Depends(require_role(["admin", "moderator"]))])
def create_product(payload: ProductCreateIn):
    try:
        pid = svc.create_product(ProductIn(**payload.model_dump()))
        return {"product_id": pid}
    except MerchError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/products", dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))]
)
def list_products(
    only_active: bool = True, category: str | None = None, band_id: int | None = None
):
    return svc.list_products(only_active=only_active, category=category, band_id=band_id)


@router.patch(
    "/products/{product_id}", dependencies=[Depends(require_role(["admin", "moderator"]))]
)
def update_product(product_id: int, fields: dict):
    try:
        svc.update_product(product_id, **fields)
        return {"ok": True}
    except MerchError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/skus", dependencies=[Depends(require_role(["admin", "moderator"]))])
def create_sku(payload: SKUCreateIn):
    try:
        sid = svc.create_sku(SKUIn(**payload.model_dump()))
        return {"sku_id": sid}
    except MerchError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/skus/{product_id}",
    dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))],
)
def list_skus(product_id: int, only_active: bool = True):
    return svc.list_skus(product_id, only_active=only_active)


@router.patch("/skus/{sku_id}", dependencies=[Depends(require_role(["admin", "moderator"]))])
def update_sku(sku_id: int, fields: dict):
    try:
        svc.update_sku(sku_id, **fields)
        return {"ok": True}
    except MerchError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/purchase", dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))]
)
def purchase(payload: PurchaseIn):
    try:
        order_id = svc.purchase(
            buyer_user_id=payload.buyer_user_id,
            items=[i.model_dump() for i in payload.items],
            shipping_address=payload.shipping_address,
        )
        return {"order_id": order_id}
    except MerchError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refund/{order_id}", dependencies=[Depends(require_role(["admin", "moderator"]))])
def refund(order_id: int, reason: str = ""):
    try:
        return svc.refund_order(order_id, reason)
    except MerchError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/orders/{order_id}",
    dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))],
)
def get_order(order_id: int):
    try:
        return svc.get_order(order_id)
    except MerchError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/orders/user/{buyer_user_id}",
    dependencies=[Depends(require_role(["admin", "moderator", "band_member"]))],
)
def list_orders_for_user(buyer_user_id: int):
    return svc.list_orders_for_user(buyer_user_id)
