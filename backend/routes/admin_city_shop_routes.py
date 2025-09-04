from fastapi import APIRouter, Depends, HTTPException, Request

from backend.auth.dependencies import get_current_user_id, require_role
from backend.services.admin_audit_service import audit_dependency
from backend.services.city_shop_service import CityShopService

router = APIRouter(
    prefix="/city-shops", tags=["AdminCityShops"], dependencies=[Depends(audit_dependency)]
)
svc = CityShopService()


async def _ensure_admin(req: Request) -> None:
    admin_id = await get_current_user_id(req)
    await require_role(["admin"], admin_id)


@router.post("/")
async def create_shop(payload: dict, req: Request):
    await _ensure_admin(req)
    city = payload.get("city", "")
    name = payload.get("name", "")
    return svc.create_shop(city=city, name=name)


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
    svc.add_item(shop_id, item_id, qty)
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


@router.post("/{shop_id}/books")
async def add_book(shop_id: int, payload: dict, req: Request):
    await _ensure_admin(req)
    book_id = int(payload.get("book_id"))
    qty = int(payload.get("quantity", 1))
    svc.add_book(shop_id, book_id, qty)
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

