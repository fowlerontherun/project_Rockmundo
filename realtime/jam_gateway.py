"""WebSocket relay for collaborative jam sessions."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict

try:  # pragma: no cover - explicit failure if FastAPI missing
    from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
except ModuleNotFoundError as exc:  # pragma: no cover - FastAPI required
    raise ImportError("FastAPI must be installed to use backend.realtime.jam_gateway") from exc

from backend.services.jam_service import JamService
from .gateway import get_current_user_id_dep
from backend.monitoring.websocket import track_connect, track_disconnect, track_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jam", tags=["realtime"])

# Shared service instance
try:
    jam_service = JamService()
except RuntimeError:
    logger.exception("JamService initialization failed")
    jam_service = None


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
    await track_connect()
    if jam_service is None:  # pragma: no cover - init failure
        raise RuntimeError("JamService unavailable")
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
            await track_message()
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
            elif op == "pause_stream":
                jam_service.pause_stream(session_id, user_id)
                await hub.publish(session_id, {"type": "stream_paused", "user_id": user_id})
            elif op == "resume_stream":
                jam_service.resume_stream(session_id, user_id)
                await hub.publish(session_id, {"type": "stream_resumed", "user_id": user_id})
            elif op == "invite":
                jam_service.invite(session_id, user_id, int(msg.get("invitee_id", 0)))
                await hub.publish(
                    session_id, {"type": "invited", "user_id": int(msg.get("invitee_id", 0))}
                )
            elif op == "ping":
                await ws.send_text(json.dumps({"op": "pong"}))
    except WebSocketDisconnect:  # pragma: no cover - network
        pass
    finally:
        await hub.unsubscribe(session_id, user_id)
        jam_service.leave_session(session_id, user_id)
        await hub.publish(session_id, {"type": "left", "user_id": user_id})
        outbound_task.cancel()
        await track_disconnect()
