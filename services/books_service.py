"""Service for managing skill books and reading sessions."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from models.book import Book
from models.skill import Skill
from models.learning_method import LearningMethod
from backend.services.skill_service import skill_service
from backend.models.book import Book
from backend.models.skill import Skill
from backend.models.learning_method import LearningMethod
from services.skill_service import skill_service


class BooksService:
    def __init__(self) -> None:
        self._books: Dict[int, Book] = {}
        self._inventories: Dict[int, List[int]] = {}
        self._id_seq = 1

    # ------------------------------------------------------------------
    # Book CRUD / inventory helpers
    def list_books(self) -> List[Book]:
        return list(self._books.values())

    def create_book(self, book: Book) -> Book:
        book.id = self._id_seq
        self._books[book.id] = book
        self._id_seq += 1
        return book

    def get_book(self, book_id: int) -> Book:
        book = self._books.get(book_id)
        if not book:
            raise ValueError("Book not found")
        return book

    def add_to_inventory(self, user_id: int, book_id: int) -> None:
        if book_id not in self._books:
            raise ValueError("invalid book")
        self._inventories.setdefault(user_id, []).append(book_id)

    def decrement_stock(self, book_id: int, quantity: int = 1) -> None:
        book = self.get_book(book_id)
        if book.stock < quantity:
            raise ValueError("not enough stock")
        book.stock -= quantity

    def list_inventory(self, user_id: int) -> List[Book]:
        return [self._books[i] for i in self._inventories.get(user_id, [])]

    # ------------------------------------------------------------------
    # Reading sessions
    def queue_reading(self, user_id: int, book_id: int, skill: Skill, hours: int) -> dict:
        """Queue a reading session that will grant skill XP when completed."""

        if book_id not in self._inventories.get(user_id, []):
            raise ValueError("book not in inventory")

        run_at = datetime.utcnow() + timedelta(hours=hours)
        params = {
            "user_id": user_id,
            "book_id": book_id,
            "skill": {
                "id": skill.id,
                "name": skill.name,
                "category": skill.category,
                "parent_id": skill.parent_id,
            },
            "hours": hours,
        }

        from services.scheduler_service import schedule_task

        return schedule_task("complete_reading", params, run_at.isoformat())

    def complete_reading(self, user_id: int, book_id: int, skill: dict, hours: int) -> dict:
        book = self._books.get(book_id)
        if not book:
            return {"status": "error", "message": "book not found"}

        sk = Skill(**skill)
        skill_service.train_with_method(user_id, sk, LearningMethod.BOOK, hours, book)

        inv = self._inventories.get(user_id, [])
        if book_id in inv:
            inv.remove(book_id)

        return {"status": "ok"}


books_service = BooksService()

__all__ = ["BooksService", "books_service"]

