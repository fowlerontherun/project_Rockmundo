from __future__ import annotations

import time
from typing import Dict, Tuple

from core.config import settings

from fastapi import HTTPException


class RateLimitMiddleware:
    """Simple per-client request rate limiting middleware.

    Uses a token bucket that refills every minute. The storage backend can be an
    in-memory dictionary or Redis. The middleware is lightweight and suitable
    for the testing environment where a full ASGI stack may not be available.
    """

    def __init__(
        self,
        limit: int | None = None,
        backend: str | None = None,
    ) -> None:
        self.limit = limit or settings.rate_limit.requests_per_min
        self.backend = (backend or settings.rate_limit.storage).lower()

        self._memory: Dict[str, Tuple[int, float]] = {}
        self._redis = None
        if self.backend == "redis":
            try:  # pragma: no cover - redis optional in tests
                import redis.asyncio as aioredis

                self._redis = aioredis.from_url(settings.rate_limit.redis_url)
            except Exception:  # fall back to memory if redis unavailable
                self.backend = "memory"

    async def _allow(self, key: str) -> bool:
        now = time.time()
        if self.backend == "redis" and self._redis is not None:
            count = await self._redis.incr(key)
            if count == 1:
                await self._redis.expire(key, 60)
            return count <= self.limit

        # In-memory store
        count, start = self._memory.get(key, (0, now))
        if now - start >= 60:
            count, start = 0, now
        count += 1
        self._memory[key] = (count, start)
        return count <= self.limit

    async def dispatch(self, request, call_next):
        client = getattr(request, "client", None)
        host = getattr(client, "host", "anonymous")
        key = f"rl:{host}"

        if not await self._allow(key):
            raise HTTPException(status_code=429, detail="Too Many Requests")

        return await call_next(request)

