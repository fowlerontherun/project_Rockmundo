"""WebSocket channel for encore voting."""
from __future__ import annotations

import asyncio
import json
from typing import Dict

try:  # pragma: no cover - explicit failure if FastAPI missing
    from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
except ModuleNotFoundError as exc:  # pragma: no cover - FastAPI required
    raise ImportError("FastAPI must be installed to use backend.realtime.polling") from exc

from .gateway import get_current_user_id_dep

router = APIRouter(prefix="/encore", tags=["realtime"])


class _Subscriber:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[str] = asyncio.Queue()

    async def send(self, message: str) -> None:
        await self.queue.put(message)

    async def stream(self):
        while True:
            yield await self.queue.get()


class PollHub:
    def __init__(self) -> None:
        self._subs: Dict[str, Dict[int, _Subscriber]] = {}
        self._votes: Dict[str, Dict[str, int]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, poll_id: str, user_id: int, sub: _Subscriber) -> None:
        async with self._lock:
            self._subs.setdefault(poll_id, {})[user_id] = sub

    async def unsubscribe(self, poll_id: str, user_id: int) -> None:
        async with self._lock:
            subs = self._subs.get(poll_id)
            if subs:
                subs.pop(user_id, None)
                if not subs:
                    self._subs.pop(poll_id, None)

    async def vote(self, poll_id: str, option: str) -> Dict[str, int]:
        async with self._lock:
            poll = self._votes.setdefault(poll_id, {})
            poll[option] = poll.get(option, 0) + 1
            leaderboard = dict(sorted(poll.items(), key=lambda kv: kv[1], reverse=True))
            subs = list(self._subs.get(poll_id, {}).values())
        msg = json.dumps({"type": "leaderboard", "votes": leaderboard}, separators=(",", ":"))
        for s in subs:
            await s.send(msg)
        return leaderboard

    def results(self, poll_id: str) -> Dict[str, int]:
        poll = self._votes.get(poll_id, {})
        return dict(sorted(poll.items(), key=lambda kv: kv[1], reverse=True))

    def clear(self, poll_id: str) -> None:
        self._votes.pop(poll_id, None)


poll_hub = PollHub()


@router.websocket("/ws/{poll_id}")
async def encore_poll_ws(ws: WebSocket, poll_id: str, user_id: int = Depends(get_current_user_id_dep)) -> None:
    await ws.accept()
    sub = _Subscriber()
    await poll_hub.subscribe(poll_id, user_id, sub)

    async def pump() -> None:
        async for msg in sub.stream():
            await ws.send_text(msg)

    outbound = asyncio.create_task(pump())
    try:
        while True:
            raw = await ws.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_text(json.dumps({"error": "invalid_json"}))
                continue
            vote = payload.get("vote")
            if vote is not None:
                await poll_hub.vote(poll_id, str(vote))
    except WebSocketDisconnect:  # pragma: no cover - network event
        pass
    finally:
        outbound.cancel()
        await poll_hub.unsubscribe(poll_id, user_id)
