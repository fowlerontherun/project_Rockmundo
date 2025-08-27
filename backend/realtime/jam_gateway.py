"""WebSocket relay for collaborative jam sessions."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict

try:  # pragma: no cover - used in real app
    from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Header
except Exception:  # pragma: no cover - fallback for tests without FastAPI
    class APIRouter:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def websocket(self, path: str):
            def decorator(func):
                return func

            return decorator

    def Depends(dep):  # type: ignore
        return dep

    class WebSocket:  # type: ignore
        async def accept(self):
            pass

        async def send_text(self, text: str):
            pass

        async def receive_text(self) -> str:
            return ""

    class WebSocketDisconnect(Exception):
        pass

    def Header(default=None, alias=None):  # type: ignore
        return default


async def get_current_user_id_dep(  # pragma: no cover - simple fallback
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> int:
    if x_user_id:
        return int(x_user_id)
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return int(parts[1])
    return 0

from backend.services.jam_service import JamService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jam", tags=["realtime"])

# Shared service instance
jam_service = JamService()


class _Subscriber:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[str] = asyncio.Queue()

    async def send(self, message: str) -> None:
        await self.queue.put(message)

    async def stream(self):
        while True:
            yield await self.queue.get()


class JamSessionHub:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._subs: Dict[str, Dict[int, _Subscriber]] = {}

    async def subscribe(self, session_id: str, user_id: int, sub: _Subscriber) -> None:
        async with self._lock:
            self._subs.setdefault(session_id, {})[user_id] = sub

    async def unsubscribe(self, session_id: str, user_id: int) -> None:
        async with self._lock:
            subs = self._subs.get(session_id)
            if subs:
                subs.pop(user_id, None)
                if not subs:
                    self._subs.pop(session_id, None)

    async def publish(self, session_id: str, payload: Dict[str, Any]) -> None:
        message = json.dumps(payload, separators=(",", ":"))
        async with self._lock:
            subs = list(self._subs.get(session_id, {}).values())
        for s in subs:
            await s.send(message)


hub = JamSessionHub()


@router.websocket("/ws/{session_id}")
async def jam_ws(ws: WebSocket, session_id: str, user_id: int = Depends(get_current_user_id_dep)) -> None:
    await ws.accept()
    sub = _Subscriber()
    await hub.subscribe(session_id, user_id, sub)

    async def pump() -> None:
        async for msg in sub.stream():
            await ws.send_text(msg)

    outbound_task = asyncio.create_task(pump())
    jam_service.join_session(session_id, user_id)
    await hub.publish(session_id, {"type": "joined", "user_id": user_id})

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({"error": "invalid_json"}))
                continue

            op = msg.get("op")
            if op == "start_stream":
                stream = jam_service.start_stream(
                    session_id,
                    user_id,
                    msg.get("stream_id", ""),
                    msg.get("codec", ""),
                    bool(msg.get("premium")),
                )
                await hub.publish(
                    session_id,
                    {"type": "stream_started", "user_id": user_id, "stream": stream.__dict__},
                )
            elif op == "stop_stream":
                jam_service.stop_stream(session_id, user_id)
                await hub.publish(session_id, {"type": "stream_stopped", "user_id": user_id})
            elif op == "ping":
                await ws.send_text(json.dumps({"op": "pong"}))
    except WebSocketDisconnect:  # pragma: no cover - network
        pass
    finally:
        await hub.unsubscribe(session_id, user_id)
        jam_service.leave_session(session_id, user_id)
        await hub.publish(session_id, {"type": "left", "user_id": user_id})
        outbound_task.cancel()
