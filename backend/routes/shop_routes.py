from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user_id, require_role
from backend.services.economy_service import EconomyService, EconomyError
from backend.services.item_service import item_service
from backend.services.books_service import books_service

router = APIRouter(prefix="/shop", tags=["Shop"])

_economy = EconomyService()
_economy.ensure_schema()


async def _current_user(user_id: int = Depends(get_current_user_id)) -> int:
    await require_role(["user", "band_member", "moderator", "admin"], user_id)
    return user_id


class PurchaseIn(BaseModel):
    owner_user_id: int
    quantity: int = 1


@router.post("/items/{item_id}/purchase")
def purchase_item(item_id: int, payload: PurchaseIn, user_id: int = Depends(_current_user)):
    try:
        item = item_service.get_item(item_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.stock < payload.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    total = item.price_cents * payload.quantity
    try:
        _economy.transfer(user_id, payload.owner_user_id, total)
    except EconomyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    item_service.decrement_stock(item_id, payload.quantity)
    item_service.add_to_inventory(user_id, item_id, payload.quantity)
    return {"status": "ok", "total_cents": total}


@router.post("/books/{book_id}/purchase")
def purchase_book(book_id: int, payload: PurchaseIn, user_id: int = Depends(_current_user)):
    try:
        book = books_service.get_book(book_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.stock < payload.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    total = book.price_cents * payload.quantity
    try:
        _economy.transfer(user_id, payload.owner_user_id, total)
    except EconomyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    books_service.decrement_stock(book_id, payload.quantity)
    for _ in range(payload.quantity):
        books_service.add_to_inventory(user_id, book_id)
    return {"status": "ok", "total_cents": total}
