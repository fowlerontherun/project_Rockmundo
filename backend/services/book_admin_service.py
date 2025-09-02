"""Admin service for managing books in SQLite."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

from backend.models.book import Book

DB_PATH = Path(__file__).resolve().parents[1] / "rockmundo.db"


class BookAdminService:
    """CRUD helpers for skill books."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = str(db_path or DB_PATH)
        self.ensure_schema()

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    rarity TEXT NOT NULL,
                    max_skill_level INTEGER NOT NULL
                )
                """,
            )
            conn.commit()

    # ------------------------------------------------------------------
    def list_books(self) -> List[Book]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, title, genre, rarity, max_skill_level FROM books ORDER BY id"
            )
            rows = cur.fetchall()
            return [Book(**dict(row)) for row in rows]

    # ------------------------------------------------------------------
    def create_book(self, book: Book) -> Book:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO books (title, genre, rarity, max_skill_level) VALUES (?, ?, ?, ?)",
                (book.title, book.genre, book.rarity, book.max_skill_level),
            )
            book.id = cur.lastrowid
            conn.commit()
            return book

    # ------------------------------------------------------------------
    def update_book(self, book_id: int, **changes) -> Book:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT id, title, genre, rarity, max_skill_level FROM books WHERE id = ?",
                (book_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Book not found")
            data = dict(row)
            for k, v in changes.items():
                if k in data and v is not None:
                    data[k] = v
            cur.execute(
                "UPDATE books SET title=?, genre=?, rarity=?, max_skill_level=? WHERE id=?",
                (
                    data["title"],
                    data["genre"],
                    data["rarity"],
                    data["max_skill_level"],
                    book_id,
                ),
            )
            conn.commit()
            return Book(**data)

    # ------------------------------------------------------------------
    def delete_book(self, book_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM books WHERE id=?", (book_id,))
            conn.commit()

    # ------------------------------------------------------------------
    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM books")
            conn.commit()


book_admin_service = BookAdminService()


def get_book_admin_service() -> BookAdminService:
    return book_admin_service


__all__ = ["BookAdminService", "book_admin_service", "get_book_admin_service"]
