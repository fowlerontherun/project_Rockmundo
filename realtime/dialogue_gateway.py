"""WebSocket gateway for live dialogue sessions with NPCs."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from backend.models.dialogue import DialogueMessage
from backend.realtime.gateway import get_current_user_id_dep
from backend.monitoring.websocket import track_connect, track_disconnect, track_message
from services.dialogue_service import DialogueService

router = APIRouter(prefix="/dialogue", tags=["dialogue"])


@router.websocket("/ws/{npc_id}")
async def dialogue_ws(
    ws: WebSocket,
    npc_id: str,
    user_id: int = Depends(get_current_user_id_dep),
) -> None:
    await ws.accept()
    await track_connect()
    service = DialogueService()
    history: List[DialogueMessage] = []
    try:
        while True:
            user_text = await ws.receive_text()
            await track_message()
            history.append(DialogueMessage(role="user", content=user_text))
            reply = await service.generate_reply(history)
            history.append(reply)
            await ws.send_text(reply.content)
    except WebSocketDisconnect:  # pragma: no cover - network event
        return
    finally:
        await track_disconnect()
