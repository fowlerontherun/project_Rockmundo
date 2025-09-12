"""WebSocket gateway for admin economy and moderation alerts."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Set

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from .gateway import hub, get_current_user_id_dep
from backend.monitoring.websocket import track_connect, track_disconnect, track_message

try:  # pragma: no cover - fallback during tests
    from backend.auth.dependencies import require_permission
except Exception:  # pragma: no cover
    async def require_permission(roles, user_id):  # type: ignore
        if user_id != 1:
            raise HTTPException(status_code=403, detail="Forbidden")
        return True

router = APIRouter(prefix="/admin/realtime", tags=["AdminRealtime"])

ECONOMY_TOPIC = "admin:economy"
MODERATION_TOPIC = "admin:moderation"


class _Subscriber:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[str] = asyncio.Queue()

    async def send(self, message: str) -> None:
        await self.queue.put(message)

    async def stream(self):
        while True:
            yield await self.queue.get()


@router.websocket("/ws")
async def admin_ws(
    ws: WebSocket,
    user_id: int = Depends(get_current_user_id_dep),
) -> None:
    """Single admin websocket that can subscribe to multiple topics."""
    await ws.accept()
    await track_connect()
    await require_permission(["admin", "moderator"], user_id)

    sub = _Subscriber()
    topics: Set[str] = set()

    async def _join(t: str) -> None:
        if t in (ECONOMY_TOPIC, MODERATION_TOPIC):
            await hub.subscribe(t, sub)
            topics.add(t)

    async def _leave(t: str) -> None:
        if t in topics:
            await hub.unsubscribe(t, sub)
            topics.discard(t)

    async def pump() -> None:
        async for msg in sub.stream():
            await ws.send_text(msg)

    task = asyncio.create_task(pump())
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
            if op == "subscribe":
                for t in msg.get("topics", []):
                    if t == "economy":
                        await _join(ECONOMY_TOPIC)
                    elif t == "moderation":
                        await _join(MODERATION_TOPIC)
                await ws.send_text(json.dumps({"ok": True, "subscribed": sorted(topics)}))
            elif op == "unsubscribe":
                for t in msg.get("topics", []):
                    if t == "economy":
                        await _leave(ECONOMY_TOPIC)
                    elif t == "moderation":
                        await _leave(MODERATION_TOPIC)
                await ws.send_text(json.dumps({"ok": True, "subscribed": sorted(topics)}))
            elif op == "ping":
                await ws.send_text(json.dumps({"op": "pong"}))
            else:
                await ws.send_text(json.dumps({"error": "unsupported_op"}))
    except WebSocketDisconnect:  # pragma: no cover - network event
        pass
    finally:
        task.cancel()
        for t in list(topics):
            await hub.unsubscribe(t, sub)
        await track_disconnect()


async def publish_economy_alert(event: Dict[str, Any]) -> int:
    """Publish an economy alert to connected admins."""
    payload = {"type": "economy_alert", **event}
    return await hub.publish(ECONOMY_TOPIC, payload)


async def publish_moderation_alert(event: Dict[str, Any]) -> int:
    """Publish a moderation alert to connected admins."""
    payload = {"type": "moderation_alert", **event}
    return await hub.publish(MODERATION_TOPIC, payload)
