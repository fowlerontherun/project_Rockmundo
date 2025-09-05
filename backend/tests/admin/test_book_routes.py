import asyncio
import pytest
from fastapi import HTTPException, Request

from backend.routes.admin_book_routes import (
    BookIn,
    create_book,
    delete_book,
    list_books,
    update_book,
    svc,
)


def test_admin_book_routes_require_admin():
    req = Request({"type": "http", "headers": []})
    payload = BookIn(title="t", genre="g", rarity="common", max_skill_level=1)
    with pytest.raises(HTTPException):
        asyncio.run(list_books(req))
    with pytest.raises(HTTPException):
        asyncio.run(create_book(payload, req))
    with pytest.raises(HTTPException):
        asyncio.run(update_book(1, payload, req))
    with pytest.raises(HTTPException):
        asyncio.run(delete_book(1, req))


def test_admin_book_routes_crud(monkeypatch, tmp_path):
    async def fake_current_user(req):
        return 1

    async def fake_require_permission(roles, user_id):
        return True

    monkeypatch.setattr(
        "backend.routes.admin_book_routes.get_current_user_id", fake_current_user
    )
    monkeypatch.setattr(
        "backend.routes.admin_book_routes.require_permission", fake_require_permission
    )

    # use temporary db
    svc.db_path = str(tmp_path / "books.db")
    svc.ensure_schema()
    svc.clear()

    req = Request({"type": "http", "headers": []})
    payload = BookIn(
        title="A", genre="fiction", rarity="common", max_skill_level=5
    )
    book = asyncio.run(create_book(payload, req))
    assert book.id is not None

    books = asyncio.run(list_books(req))
    assert len(books) == 1

    upd = BookIn(
        title="B", genre="fiction", rarity="rare", max_skill_level=6
    )
    updated = asyncio.run(update_book(book.id, upd, req))
    assert updated.title == "B"
    assert updated.rarity == "rare"

    res = asyncio.run(delete_book(book.id, req))
    assert res == {"status": "deleted"}
    assert asyncio.run(list_books(req)) == []
