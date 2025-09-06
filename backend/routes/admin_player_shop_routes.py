from fastapi import APIRouter, Depends, HTTPException, Request

from backend.auth.dependencies import get_current_user_id, require_permission
from backend.services.admin_audit_service import audit_dependency
from backend.services.city_shop_service import CityShopService

router = APIRouter(
    prefix="/economy/player-shops",
    tags=["AdminPlayerShops"],
    dependencies=[Depends(audit_dependency)],
)
svc = CityShopService()


async def _current_user(req: Request) -> int:
    uid = await get_current_user_id(req)
    await require_permission(["user", "band_member", "moderator", "admin"], uid)
    return uid


async def _ensure_owner(shop_id: int, req: Request) -> int:
    uid = await _current_user(req)
    shop = svc.get_shop(shop_id)
    if not shop or shop.get("owner_user_id") != uid:
        raise HTTPException(status_code=403, detail="Not shop owner")
    return uid


async def _ensure_admin(req: Request) -> None:
    uid = await get_current_user_id(req)
    await require_permission(["admin"], uid)


@router.get("/")
async def list_owned_shops(req: Request):
    uid = await _current_user(req)
    return svc.list_shops(owner_user_id=uid)


@router.get("/{shop_id}/items")
async def list_items(shop_id: int, req: Request):
    await _ensure_owner(shop_id, req)
    return svc.list_items(shop_id)


@router.get("/{shop_id}/books")
async def list_books(shop_id: int, req: Request):
    await _ensure_owner(shop_id, req)
    return svc.list_books(shop_id)


@router.put("/{shop_id}/items/{item_id}")
async def update_item(shop_id: int, item_id: int, payload: dict, req: Request):
    await _ensure_owner(shop_id, req)
    qty = payload.get("quantity")
    price = payload.get("price_cents")
    try:
        svc.update_item(shop_id, item_id, quantity=qty, price_cents=price)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok"}


@router.put("/{shop_id}/books/{book_id}")
async def update_book(shop_id: int, book_id: int, payload: dict, req: Request):
    await _ensure_owner(shop_id, req)
    qty = payload.get("quantity")
    price = payload.get("price_cents")
    try:
        svc.update_book(shop_id, book_id, quantity=qty, price_cents=price)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok"}


@router.get("/{shop_id}/revenue")
async def revenue(shop_id: int, req: Request):
    await _ensure_owner(shop_id, req)
    return {"revenue_cents": svc.get_revenue(shop_id)}


@router.post("/{shop_id}/transfer")
async def transfer(shop_id: int, payload: dict, req: Request):
    await _ensure_admin(req)
    new_owner = payload.get("owner_user_id")
    shop = svc.transfer_ownership(shop_id, new_owner)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop
