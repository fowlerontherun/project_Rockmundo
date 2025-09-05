from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

try:
    from auth.dependencies import require_role
except Exception:  # pragma: no cover
    def require_role(_: List[str]):
        async def _noop() -> None:  # type: ignore[return-value]
            return None

        return _noop

import asyncio
from services.sales_service import SalesError, SalesService

router = APIRouter(prefix="/sales", tags=["Sales"])

svc = SalesService()
asyncio.run(svc.ensure_schema())


class DigitalSaleIn(BaseModel):
    buyer_user_id: int
    work_type: str  # 'song' | 'album'
    work_id: int
    price_cents: int
    currency: str = "USD"
    source: str | None = "store"


@router.post(
    "/digital",
    dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))],
)
async def record_digital(payload: DigitalSaleIn) -> dict[str, int]:
    """Record a digital song or album sale."""

    try:
        sid = await svc.record_digital_sale(**payload.model_dump())
    except SalesError as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc))
    return {"sale_id": sid}


@router.get(
    "/digital/{work_type}/{work_id}",
    dependencies=[Depends(require_role(["admin", "moderator"]))],
)
async def list_digital_sales(work_type: str, work_id: int):
    """List digital sales for a work."""

    return await svc.list_digital_sales_for_work(work_type, work_id)


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


@router.post(
    "/vinyl/sku",
    dependencies=[Depends(require_role(["admin", "moderator"]))],
)
async def create_vinyl_sku(payload: VinylSkuIn) -> dict[str, int]:
    try:
        sku_id = await svc.create_vinyl_sku(**payload.model_dump())
    except SalesError as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc))
    return {"sku_id": sku_id}


@router.get(
    "/vinyl/sku/{album_id}",
    dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))],
)
async def list_vinyl_skus(album_id: int):
    return await svc.list_vinyl_skus(album_id)


@router.post(
    "/vinyl/purchase",
    dependencies=[Depends(require_role(["band_member", "admin", "moderator"]))],
)
async def purchase_vinyl(payload: VinylPurchaseIn) -> dict[str, int]:
    try:
        order_id = await svc.purchase_vinyl(
            buyer_user_id=payload.buyer_user_id,
            items=[i.model_dump() for i in payload.items],
            shipping_address=payload.shipping_address,
        )
    except SalesError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"order_id": order_id}


@router.post(
    "/vinyl/refund/{order_id}",
    dependencies=[Depends(require_role(["admin", "moderator"]))],
)
async def refund_vinyl(order_id: int, reason: str = "") -> dict[str, bool]:
    try:
        await svc.refund_vinyl_order(order_id, reason)
    except SalesError as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ok": True}

