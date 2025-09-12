from fastapi import APIRouter, Depends, HTTPException, Request

from auth.dependencies import get_current_user_id, require_permission
from services.admin_audit_service import audit_dependency
from services.city_shop_service import CityShopService
from services.shop_restock_service import schedule_restock

router = APIRouter(
    prefix="/city-shops", tags=["AdminCityShops"], dependencies=[Depends(audit_dependency)]
)
svc = CityShopService()


async def _ensure_admin(req: Request) -> None:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)


@router.post("/")
async def create_shop(payload: dict, req: Request):
    await _ensure_admin(req)
    city = payload.get("city", "")
    name = payload.get("name", "")
    owner = payload.get("owner_user_id")
    return svc.create_shop(city=city, name=name, owner_user_id=owner)


@router.get("/")
async def list_shops(req: Request, city: str | None = None):
    await _ensure_admin(req)
    return svc.list_shops(city)


@router.put("/{shop_id}")
async def update_shop(shop_id: int, payload: dict, req: Request):
    await _ensure_admin(req)
    shop = svc.update_shop(shop_id, payload)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


@router.delete("/{shop_id}")
async def delete_shop(shop_id: int, req: Request):
    await _ensure_admin(req)
    if not svc.delete_shop(shop_id):
        raise HTTPException(status_code=404, detail="Shop not found")
    return {"status": "deleted"}


@router.post("/{shop_id}/items")
async def add_item(shop_id: int, payload: dict, req: Request):
    await _ensure_admin(req)
    item_id = int(payload.get("item_id"))
    qty = int(payload.get("quantity", 1))
    price = int(payload.get("price_cents", 0))
    svc.add_item(shop_id, item_id, qty, price)
    return {"status": "ok"}


@router.put("/{shop_id}/items/{item_id}")
async def update_item(shop_id: int, item_id: int, payload: dict, req: Request):
    await _ensure_admin(req)
    qty = payload.get("quantity")
    price = payload.get("price_cents")
    try:
        svc.update_item(shop_id, item_id, quantity=qty, price_cents=price)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok"}


@router.get("/{shop_id}/items")
async def list_items(shop_id: int, req: Request):
    await _ensure_admin(req)
    return svc.list_items(shop_id)


@router.delete("/{shop_id}/items/{item_id}")
async def remove_item(shop_id: int, item_id: int, req: Request, quantity: int = 1):
    await _ensure_admin(req)
    try:
        svc.remove_item(shop_id, item_id, quantity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok"}


@router.put("/{shop_id}/items/{item_id}/restock")
async def set_item_restock(shop_id: int, item_id: int, payload: dict, req: Request):
    await _ensure_admin(req)
    interval = payload.get("interval")
    qty = payload.get("quantity")
    svc.set_item_restock(shop_id, item_id, interval, qty)
    if interval and qty:
        schedule_restock(shop_id, "item", item_id, int(interval), int(qty))
    return {"status": "ok"}


@router.post("/{shop_id}/books")
async def add_book(shop_id: int, payload: dict, req: Request):
    await _ensure_admin(req)
    book_id = int(payload.get("book_id"))
    qty = int(payload.get("quantity", 1))
    price = int(payload.get("price_cents", 0))
    svc.add_book(shop_id, book_id, qty, price)
    return {"status": "ok"}


@router.put("/{shop_id}/books/{book_id}")
async def update_book(shop_id: int, book_id: int, payload: dict, req: Request):
    await _ensure_admin(req)
    qty = payload.get("quantity")
    price = payload.get("price_cents")
    try:
        svc.update_book(shop_id, book_id, quantity=qty, price_cents=price)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok"}


@router.get("/{shop_id}/books")
async def list_books(shop_id: int, req: Request):
    await _ensure_admin(req)
    return svc.list_books(shop_id)


@router.delete("/{shop_id}/books/{book_id}")
async def remove_book(shop_id: int, book_id: int, req: Request, quantity: int = 1):
    await _ensure_admin(req)
    try:
        svc.remove_book(shop_id, book_id, quantity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok"}


@router.put("/{shop_id}/books/{book_id}/restock")
async def set_book_restock(shop_id: int, book_id: int, payload: dict, req: Request):
    await _ensure_admin(req)
    interval = payload.get("interval")
    qty = payload.get("quantity")
    svc.set_book_restock(shop_id, book_id, interval, qty)
    if interval and qty:
        schedule_restock(shop_id, "book", book_id, int(interval), int(qty))
    return {"status": "ok"}


@router.post("/{shop_id}/bundles")
async def add_bundle(shop_id: int, payload: dict, req: Request):
    await _ensure_admin(req)
    name = payload.get("name", "")
    price = int(payload.get("price_cents", 0))
    items = payload.get("items", [])
    promo_starts = payload.get("promo_starts")
    promo_ends = payload.get("promo_ends")
    bundle_id = svc.add_bundle(
        shop_id, name, price, items, promo_starts, promo_ends
    )
    return {"bundle_id": bundle_id}


@router.get("/{shop_id}/bundles")
async def list_bundles(shop_id: int, req: Request):
    await _ensure_admin(req)
    return svc.list_bundles(shop_id)

