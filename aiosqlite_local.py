"""Minimal stub of :mod:`aiosqlite` used for tests.

This is *not* a full implementation but provides the small subset of
functionality required by the exercises.  It wraps the standard :mod:`sqlite3`
module and executes blocking operations in a thread pool so the API mirrors
the real ``aiosqlite`` package.
"""

from __future__ import annotations

import asyncio
import sqlite3
from typing import Any, Iterable

Row = sqlite3.Row


class Cursor:
    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    async def execute(self, sql: str, params: Iterable[Any] | None = None):
        params = tuple(params or ())
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._cursor.execute, sql, params)
        return self

    async def executemany(self, sql: str, seq: Iterable[Iterable[Any]]):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._cursor.executemany, sql, list(seq))
        return self

    async def fetchone(self):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._cursor.fetchone)

    async def fetchall(self):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._cursor.fetchall)

    @property
    def lastrowid(self) -> int:
        return self._cursor.lastrowid


class Connection:
    def __init__(self, path: str):
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self.row_factory = None

    async def execute(self, sql: str, params: Iterable[Any] | None = None):
        cur = self._conn.cursor()
        if self.row_factory is not None:
            self._conn.row_factory = self.row_factory
            cur = self._conn.cursor()
        params = tuple(params or ())
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cur.execute, sql, params)
        return Cursor(cur)

    async def executemany(self, sql: str, seq: Iterable[Iterable[Any]]):
        cur = self._conn.cursor()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cur.executemany, sql, list(seq))
        return Cursor(cur)

    async def executescript(self, script: str):
        cur = self._conn.cursor()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, cur.executescript, script)
        return Cursor(cur)

    async def commit(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._conn.commit)

    async def rollback(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._conn.rollback)

    async def close(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._conn.close)

    async def __aenter__(self):  # pragma: no cover - convenience
        return self

    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover
        await self.close()

    # For synchronous wrapper
    def cursor(self) -> Cursor:  # pragma: no cover - minimal usage
        if self.row_factory is not None:
            self._conn.row_factory = self.row_factory
        return Cursor(self._conn.cursor())


async def connect(path: str) -> Connection:
    return Connection(path)

