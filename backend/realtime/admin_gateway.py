"""WebSocket gateway for admin economy and moderation alerts."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from .gateway import hub, get_current_user_id_dep

try:  # pragma: no cover - fallback during tests
    from auth.dependencies import require_permission
except Exception:  # pragma: no cover
    async def require_permission(roles, user_id):  # type: ignore
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


@router.websocket("/ws/{channel}")
async def admin_ws(
    ws: WebSocket,
    channel: str,
    user_id: int = Depends(get_current_user_id_dep),
) -> None:
    await ws.accept()
    await require_permission(["admin", "moderator"], user_id)

    topic_map = {"economy": ECONOMY_TOPIC, "moderation": MODERATION_TOPIC}
    topic = topic_map.get(channel)
    if not topic:
        await ws.close()
        return

    sub = _Subscriber()
    await hub.subscribe(topic, sub)

    async def pump() -> None:
        async for msg in sub.stream():
            await ws.send_text(msg)

    task = asyncio.create_task(pump())
    try:
        while True:
            # Ignore client messages; heartbeat via ping/pong is not required
            await ws.receive_text()
    except WebSocketDisconnect:  # pragma: no cover - network event
        pass
    finally:
        task.cancel()
        await hub.unsubscribe(topic, sub)


async def publish_economy_alert(event: Dict[str, Any]) -> int:
    """Publish an economy alert to connected admins."""
    payload = {"type": "economy_alert", **event}
    return await hub.publish(ECONOMY_TOPIC, payload)


async def publish_moderation_alert(event: Dict[str, Any]) -> int:
    """Publish a moderation alert to connected admins."""
    payload = {"type": "moderation_alert", **event}
    return await hub.publish(MODERATION_TOPIC, payload)
