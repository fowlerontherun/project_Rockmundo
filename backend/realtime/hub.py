from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, Protocol, Set, Tuple

from backend.utils.logging import get_logger
from backend.utils.metrics import Counter
from backend.utils.tracing import get_tracer

logger = get_logger(__name__)
tracer = get_tracer(__name__)
PUBLISHED = Counter(
    "realtime_messages_published_total", "Messages published via realtime hub"
)


class Subscriber(Protocol):
    """Protocol representing a subscriber that can receive messages."""

    async def send(self, message: str) -> None: ...


class RealtimeHub(Protocol):
    async def subscribe(self, topic: str, sub: Subscriber) -> None: ...
    async def unsubscribe(self, topic: str, sub: Subscriber) -> None: ...
    async def publish(self, topic: str, payload: Dict[str, Any]) -> int: ...


class InMemoryHub(RealtimeHub):
    """In-memory implementation of the realtime hub."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._topics: Dict[str, Set[Subscriber]] = {}

    async def subscribe(self, topic: str, sub: Subscriber) -> None:
        async with self._lock:
            self._topics.setdefault(topic, set()).add(sub)
            logger.debug("Subscribed to %s (count=%d)", topic, len(self._topics[topic]))

    async def unsubscribe(self, topic: str, sub: Subscriber) -> None:
        async with self._lock:
            subs = self._topics.get(topic)
            if not subs:
                return
            subs.discard(sub)
            if not subs:
                self._topics.pop(topic, None)
            logger.debug(
                "Unsubscribed from %s (remaining=%d)",
                topic,
                len(self._topics.get(topic, [])),
            )

    async def publish(self, topic: str, payload: Dict[str, Any]) -> int:
        with tracer.start_as_current_span("realtime.publish"):
            message = json.dumps(
                {"topic": topic, "ts": int(time.time() * 1000), "data": payload},
                separators=(",", ":"),
            )
            async with self._lock:
                subs = list(self._topics.get(topic, []))
            for s in subs:
                await s.send(message)
            PUBLISHED.labels().inc(len(subs))
            logger.debug("Published to %s -> %d subscribers", topic, len(subs))
            return len(subs)


class RedisHub(RealtimeHub):
    """Redis-backed realtime hub using pub/sub channels."""

    def __init__(self, url: str) -> None:
        try:
            import redis.asyncio as aioredis  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Redis backend requires redis-py") from exc

        self._redis = aioredis.from_url(url, decode_responses=True)
        self._lock = asyncio.Lock()
        self._topics: Dict[str, Set[Subscriber]] = {}
        self._listeners: Dict[str, Tuple[Any, asyncio.Task]] = {}

    async def subscribe(self, topic: str, sub: Subscriber) -> None:
        async with self._lock:
            subs = self._topics.setdefault(topic, set())
            subs.add(sub)
            if topic not in self._listeners:
                pubsub = self._redis.pubsub()
                await pubsub.subscribe(topic)

                async def reader(ps: Any, t: str) -> None:
                    try:
                        async for msg in ps.listen():
                            if msg.get("type") == "message":
                                async with self._lock:
                                    targets = list(self._topics.get(t, []))
                                for s in targets:
                                    await s.send(msg["data"])
                    except asyncio.CancelledError:
                        pass

                task = asyncio.create_task(reader(pubsub, topic))
                self._listeners[topic] = (pubsub, task)

    async def unsubscribe(self, topic: str, sub: Subscriber) -> None:
        async with self._lock:
            subs = self._topics.get(topic)
            if not subs:
                return
            subs.discard(sub)
            if not subs:
                self._topics.pop(topic, None)
                pubsub, task = self._listeners.pop(topic, (None, None))
                if pubsub is not None:
                    await pubsub.unsubscribe(topic)
                    await pubsub.close()
                if task is not None:
                    task.cancel()

    async def publish(self, topic: str, payload: Dict[str, Any]) -> int:
        with tracer.start_as_current_span("realtime.publish"):
            message = json.dumps(
                {"topic": topic, "ts": int(time.time() * 1000), "data": payload},
                separators=(",", ":"),
            )
            await self._redis.publish(topic, message)
            async with self._lock:
                count = len(self._topics.get(topic, []))
            PUBLISHED.labels().inc(count)
            logger.debug("Published to %s -> %d subscribers", topic, count)
            return count
