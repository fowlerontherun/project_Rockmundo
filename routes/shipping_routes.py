from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user_id, require_permission
from services.shipping_service import ShippingService

router = APIRouter(prefix="/shipping", tags=["Shipping"])

shipping_service = ShippingService()


async def _current_user(user_id: int = Depends(get_current_user_id)) -> int:
    await require_permission(["user", "band_member", "moderator", "admin"], user_id)
    return user_id


class TransferIn(BaseModel):
    source_shop_id: int
    dest_shop_id: int
    item_id: int
    quantity: int = 1


@router.post("/transfer")
def transfer(payload: TransferIn, user_id: int = Depends(_current_user)):
    try:
        return shipping_service.create_shipment(
            payload.source_shop_id,
            payload.dest_shop_id,
            payload.item_id,
            payload.quantity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/shipments/{shipment_id}")
def shipment_detail(shipment_id: int, user_id: int = Depends(_current_user)):
    shipment = shipping_service.get_shipment(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment


@router.get("/shipments")
def shipment_list(shop_id: int | None = None, user_id: int = Depends(_current_user)):
    return shipping_service.list_shipments(shop_id)
