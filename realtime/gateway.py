# backend/realtime/gateway.py
from __future__ import annotations

import asyncio
import json
import time
from typing import AsyncIterator, List, Optional, Set

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import StreamingResponse

from core.config import settings

from .hub import InMemoryHub, RealtimeHub, RedisHub
from monitoring.websocket import (
    TOPIC as METRICS_TOPIC,
    track_connect,
    track_disconnect,
    track_message,
)

router = APIRouter(prefix="/realtime", tags=["realtime"])

# --- Auth helpers -------------------------------------------------------------

async def _fallback_auth_header(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
) -> int:
    """
    Simple fallback for tests/local if your real auth util isn't importable.
    Priority:
      1) If a real util exists (import below), we never hit this.
      2) Else, try "X-User-Id" header with an int.
      3) Else, try "Authorization: Bearer <user_id>" with an int payload.
    """
    if x_user_id:
        try:
            return int(x_user_id)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid X-User-Id header")
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            try:
                return int(parts[1])
            except ValueError:
                raise HTTPException(status_code=401, detail="Invalid bearer token payload")
    raise HTTPException(status_code=401, detail="Missing auth")

# Try to pull your real auth dependency if present in the codebase
try:
    # Expected: your existing auth util that returns the current user's id (int)
    from core.auth import get_current_user_id as _real_get_current_user_id  # type: ignore

    async def get_current_user_id_dep(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
        request: Optional[Request] = None,
    ) -> int:
        # many FastAPI auth deps ignore args; this keeps signature flexible
        uid = _real_get_current_user_id()  # type: ignore
        if not isinstance(uid, int):
            raise HTTPException(status_code=401, detail="Auth provided non-int user id")
        return uid
except Exception:
    # Fallback path for tests/local
    async def get_current_user_id_dep(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
        x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    ) -> int:
        return await _fallback_auth_header(authorization=authorization, x_user_id=x_user_id)

# --- Pub/Sub Hub --------------------------------------------------------------


class _Subscriber:
    """A subscriber owns an asyncio.Queue of outbound events."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[str] = asyncio.Queue()

    async def send(self, message: str) -> None:
        await self.queue.put(message)

    async def stream(self) -> AsyncIterator[str]:
        # Consumer side iterator
        while True:
            msg = await self.queue.get()
            yield msg


if settings.realtime.backend == "redis":
    hub: RealtimeHub = RedisHub(settings.realtime.redis_url)
else:
    hub = InMemoryHub()

# --- Topic helpers ------------------------------------------------------------

def topic_for_user(user_id: int) -> str:
    return f"user:{user_id}"

PULSE_TOPIC = "pulse"
ADMIN_JOBS_TOPIC = "admin:jobs"

# --- WebSocket endpoint -------------------------------------------------------

@router.websocket("/ws")
async def websocket_gateway(ws: WebSocket, user_id: int = Depends(get_current_user_id_dep)) -> None:
    """
    Bi-directional WS. Client connects and automatically joins:
      - user:<user_id>
    Clients may optionally send a JSON message {"op":"subscribe","topics":["pulse", "..."]}
    to add more topics, and {"op":"unsubscribe","topics":[...]} to remove.
    Server never trusts client for user:<other_id> topics.
    """
    await ws.accept()
    await track_connect()
    sub = _Subscriber()

    # Track topics for this connection
    topics: Set[str] = set()
    async def _join(t: str) -> None:
        if t.startswith("user:"):
            # only allow the caller's own user channel
            if t != topic_for_user(user_id):
                return
        await hub.subscribe(t, sub)
        topics.add(t)

    async def _leave(t: str) -> None:
        if t in topics:
            await hub.unsubscribe(t, sub)
            topics.discard(t)

    # Always join own user topic
    await _join(topic_for_user(user_id))

    # Task: forward hub messages to client
    async def pump_outbound() -> None:
        async for m in sub.stream():
            await ws.send_text(m)

    outbound_task = asyncio.create_task(pump_outbound())

    try:
        while True:
            raw = await ws.receive_text()
            await track_message()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({"error": "invalid_json"}))
                continue

            op = msg.get("op")
            if op == "ping":
                await ws.send_text(json.dumps({"op": "pong", "ts": int(time.time() * 1000)}))
            elif op == "subscribe":
                for t in msg.get("topics", []):
                    # Only allow whitelisted non-user topics
                    if t in (PULSE_TOPIC, ADMIN_JOBS_TOPIC, METRICS_TOPIC) or t == topic_for_user(user_id):
                        await _join(t)
                await ws.send_text(json.dumps({"ok": True, "subscribed": list(sorted(topics))}))
            elif op == "unsubscribe":
                for t in msg.get("topics", []):
                    await _leave(t)
                await ws.send_text(json.dumps({"ok": True, "subscribed": list(sorted(topics))}))
            else:
                # For now, ignore client-to-server application messages.
                await ws.send_text(json.dumps({"error": "unsupported_op"}))

    except WebSocketDisconnect:
        pass
    finally:
        outbound_task.cancel()
        for t in list(topics):
            try:
                await hub.unsubscribe(t, sub)
            except Exception:
                pass
        await track_disconnect()

# --- Server-Sent Events endpoint ---------------------------------------------

async def _sse_event(data: str, event: Optional[str] = None) -> bytes:
    # SSE wire format: optional "event:" line + "data:" then blank line
    lines = []
    if event:
        lines.append(f"event: {event}")
    # data can be multi-line; split to 'data:' per line
    for line in data.splitlines() or [""]:
        lines.append(f"data: {line}")
    lines.append("")  # terminator blank line
    return ("\n".join(lines) + "\n").encode("utf-8")

@router.get("/sse")
async def sse_gateway(
    request: Request,
    user_id: int = Depends(get_current_user_id_dep),
    topics_qs: Optional[str] = None,
) -> StreamingResponse:
    """
    SSE stream. By default subscribes to user:<user_id>.
    Clients can add query ?topics=pulse,admin:jobs (comma-separated).
    """
    sub = _Subscriber()
    # minimal keep-alive every 20s so proxies don't cut us off
    keepalive_interval = 20.0

    async def gen() -> AsyncIterator[bytes]:
        # Subscribe to self + any extras
        await hub.subscribe(topic_for_user(user_id), sub)
        extras: List[str] = []
        if topics_qs:
            for raw in topics_qs.split(","):
                t = raw.strip()
                if t and (t in (PULSE_TOPIC, ADMIN_JOBS_TOPIC)):
                    await hub.subscribe(t, sub)
                    extras.append(t)

        last_keepalive = time.monotonic()

        try:
            # Initial hello
            hello = json.dumps(
                {"topic": "hello", "ts": int(time.time() * 1000), "data": {"subscribed": [topic_for_user(user_id), *extras]}}
            )
            yield await _sse_event(hello, event="hello")

            # Main loop: interleave hub messages + keepalive
            while True:
                # Send keepalive if needed
                now = time.monotonic()
                if now - last_keepalive >= keepalive_interval:
                    last_keepalive = now
                    # comment lines are allowed as heartbeats
                    yield b": keepalive\n\n"

                try:
                    msg = await asyncio.wait_for(sub.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    # loop again to potentially send keepalive
                    if await request.is_disconnected():
                        break
                    continue

                yield await _sse_event(msg, event="message")

                if await request.is_disconnected():
                    break
        finally:
            await hub.unsubscribe(topic_for_user(user_id), sub)
            for t in extras:
                await hub.unsubscribe(t, sub)

    return StreamingResponse(gen(), media_type="text/event-stream")
