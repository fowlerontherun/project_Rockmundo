"""Admin routes for managing books."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.auth.dependencies import get_current_user_id, require_permission
from backend.models.book import Book
from backend.services.admin_audit_service import audit_dependency
from backend.services.book_admin_service import BookAdminService, get_book_admin_service

router = APIRouter(
    prefix="/learning/books", tags=["AdminBooks"], dependencies=[Depends(audit_dependency)]
)
svc: BookAdminService = get_book_admin_service()


class BookIn(BaseModel):
    title: str
    genre: str
    rarity: str
    max_skill_level: int


async def _ensure_admin(req: Request) -> None:
    admin_id = await get_current_user_id(req)
    await require_permission(["admin"], admin_id)


@router.get("/")
async def list_books(req: Request) -> list[Book]:
    await _ensure_admin(req)
    return svc.list_books()


@router.post("/")
async def create_book(payload: BookIn, req: Request) -> Book:
    await _ensure_admin(req)
    book = Book(id=None, **payload.dict())
    return svc.create_book(book)


@router.put("/{book_id}")
async def update_book(book_id: int, payload: BookIn, req: Request) -> Book:
    await _ensure_admin(req)
    try:
        return svc.update_book(book_id, **payload.dict())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{book_id}")
async def delete_book(book_id: int, req: Request) -> dict[str, str]:
    await _ensure_admin(req)
    svc.delete_book(book_id)
    return {"status": "deleted"}


__all__ = ["router", "list_books", "create_book", "update_book", "delete_book", "BookIn", "svc"]
