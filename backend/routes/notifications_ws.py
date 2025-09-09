"""WebSocket endpoint for user notifications."""
from __future__ import annotations

import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from backend.realtime.gateway import (
    _Subscriber,
    get_current_user_id_dep,
    hub,
    topic_for_user,
)
from backend.monitoring.websocket import track_connect, track_disconnect, track_message

router = APIRouter(prefix="/notifications", tags=["realtime"])


@router.websocket("/ws")
async def notifications_ws(
    ws: WebSocket, user_id: int = Depends(get_current_user_id_dep)
) -> None:
    """Stream notification events for the current user.

    The handler subscribes to the realtime hub using the caller's user topic and
    forwards any published messages. Incoming messages are ignored except for
    optional ping frames.
    """

    await ws.accept()
    await track_connect()

    sub = _Subscriber()
    topic = topic_for_user(user_id)
    await hub.subscribe(topic, sub)

    async def pump() -> None:
        async for msg in sub.stream():
            await ws.send_text(msg)

    outbound = asyncio.create_task(pump())
    try:
        while True:
            try:
                raw = await ws.receive_text()
            except WebSocketDisconnect:
                break
            await track_message()
            if raw == "ping":
                await ws.send_text("pong")
    finally:
        outbound.cancel()
        await hub.unsubscribe(topic, sub)
        await track_disconnect()
