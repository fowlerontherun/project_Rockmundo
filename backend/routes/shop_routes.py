from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user_id, require_role
from backend.services.books_service import books_service
from backend.services.city_shop_service import city_shop_service
from backend.services.economy_service import EconomyError, EconomyService
from backend.services.item_service import item_service
from backend.services.loyalty_service import loyalty_service
from backend.services.shop_npc_service import shop_npc_service

router = APIRouter(prefix="/shop", tags=["Shop"])

_economy = EconomyService()
_economy.ensure_schema()


async def _current_user(user_id: int = Depends(get_current_user_id)) -> int:
    await require_role(["user", "band_member", "moderator", "admin"], user_id)
    return user_id


class PurchaseIn(BaseModel):
    owner_user_id: int
    quantity: int = 1


class SellIn(BaseModel):
    quantity: int = 1


class RepairIn(BaseModel):
    owner_user_id: int


@router.post("/items/{item_id}/purchase")
def purchase_item(item_id: int, payload: PurchaseIn, user_id: int = Depends(_current_user)):
    try:
        item = item_service.get_item(item_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.stock < payload.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    base_total = item.price_cents * payload.quantity
    discount_pct = loyalty_service.get_discount(user_id, payload.owner_user_id)
    discount_cents = int(base_total * discount_pct / 100)
    total = base_total - discount_cents
    try:
        _economy.transfer(user_id, payload.owner_user_id, total)
    except EconomyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    item_service.decrement_stock(item_id, payload.quantity)
    item_service.add_to_inventory(user_id, item_id, payload.quantity)
    earned = loyalty_service.points_for_purchase(total)
    loyalty_service.add_points(user_id, payload.owner_user_id, earned)
    return {
        "status": "ok",
        "total_cents": total,
        "discount_cents": discount_cents,
        "earned_points": earned,
    }


@router.post("/items/{item_id}/repair")
def repair_item(item_id: int, payload: RepairIn, user_id: int = Depends(_current_user)):
    try:
        item_record = item_service.get_inventory_item(user_id, item_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Item not owned")
    missing = 100 - item_record["durability"]
    if missing <= 0:
        return {"status": "ok", "maintenance_cents": 0, "new_durability": item_record["durability"]}
    fee = missing  # 1 cent per durability point
    try:
        _economy.transfer(user_id, payload.owner_user_id, fee)
    except EconomyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    new_dur = item_service.repair_item(user_id, item_id)
    return {"status": "ok", "maintenance_cents": fee, "new_durability": new_dur}


@router.post("/city/{shop_id}/items/{item_id}/sell")
def sell_item(shop_id: int, item_id: int, payload: SellIn, user_id: int = Depends(_current_user)):
    try:
        payout = city_shop_service.sell_item(shop_id, user_id, item_id, payload.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok", "payout_cents": payout}


@router.post("/books/{book_id}/purchase")
def purchase_book(book_id: int, payload: PurchaseIn, user_id: int = Depends(_current_user)):
    try:
        book = books_service.get_book(book_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.stock < payload.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    base_total = book.price_cents * payload.quantity
    discount_pct = loyalty_service.get_discount(user_id, payload.owner_user_id)
    discount_cents = int(base_total * discount_pct / 100)
    total = base_total - discount_cents
    try:
        _economy.transfer(user_id, payload.owner_user_id, total)
    except EconomyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    books_service.decrement_stock(book_id, payload.quantity)
    for _ in range(payload.quantity):
        books_service.add_to_inventory(user_id, book_id)
    earned = loyalty_service.points_for_purchase(total)
    loyalty_service.add_points(user_id, payload.owner_user_id, earned)
    return {
        "status": "ok",
        "total_cents": total,
        "discount_cents": discount_cents,
        "earned_points": earned,
    }


@router.post("/city/{shop_id}/books/{book_id}/sell")
def sell_book(shop_id: int, book_id: int, payload: SellIn, user_id: int = Depends(_current_user)):
    try:
        payout = city_shop_service.sell_book(shop_id, user_id, book_id, payload.quantity)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok", "payout_cents": payout}


@router.get("/npc/dialogue")
def get_shop_dialogue(choices: str = ""):
    """Return dialogue lines and possible responses for the shop NPC."""

    try:
        parsed = [int(c) for c in choices.split(",") if c]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid choices")
    return shop_npc_service.get_dialogue(parsed)


@router.get("/daily-special")
def get_daily_special():
    """Return today's rotating promotion."""

    return shop_npc_service.get_daily_special()
