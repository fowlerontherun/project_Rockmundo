import asyncio
import json
from fastapi import WebSocketDisconnect

from backend.realtime.gateway import websocket_gateway
from backend.monitoring.websocket import (
    CONNECTIONS_ACTIVE,
    CONNECTIONS_TOTAL,
    MESSAGES_TOTAL,
)


class DummyWebSocket:
    def __init__(self) -> None:
        self.sent = []
        self._queue = asyncio.Queue()

    async def accept(self) -> None:
        pass

    async def send_text(self, text: str) -> None:
        self.sent.append(text)

    async def receive_text(self) -> str:
        item = await self._queue.get()
        if isinstance(item, Exception):
            raise item
        return item

    def queue(self, text: str | Exception) -> None:
        self._queue.put_nowait(text)


def test_metrics_increment_on_websocket_flow():
    CONNECTIONS_TOTAL._values.clear()
    CONNECTIONS_ACTIVE._values.clear()
    MESSAGES_TOTAL._values.clear()

    async def run() -> None:
        ws = DummyWebSocket()
        ws.queue(json.dumps({"op": "ping"}))
        ws.queue(WebSocketDisconnect())
        await websocket_gateway(ws, user_id=1)

    asyncio.run(run())
    assert CONNECTIONS_TOTAL._values.get((), 0) == 1
    assert MESSAGES_TOTAL._values.get((), 0) == 1
    assert CONNECTIONS_ACTIVE._values.get((), 0) == 0
