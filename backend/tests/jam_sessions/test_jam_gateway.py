import asyncio
import json
from contextlib import suppress

import pytest

from backend.realtime.jam_gateway import jam_ws, jam_service


class FakeWebSocket:
    def __init__(self):
        self.sent_queue: asyncio.Queue[str] = asyncio.Queue()
        self.receive_queue: asyncio.Queue[str] = asyncio.Queue()

    async def accept(self):
        pass

    async def send_text(self, text: str):
        await self.sent_queue.put(text)

    async def receive_text(self) -> str:
        return await self.receive_queue.get()

    def queue(self, text: str) -> None:
        self.receive_queue.put_nowait(text)


def test_jam_session_flow(tmp_path):
    async def run() -> None:
        jam_service.sessions.clear()
        jam_service.economy.db_path = str(tmp_path / "jam.db")
        jam_service.economy.ensure_schema()

        host_id = 1
        user_id = 2
        jam_service.economy.deposit(host_id, 500)
        jam_service.economy.deposit(user_id, 500)

        session = jam_service.create_session(host_id)
        jam_service.invite(session.id, host_id, user_id)

        host_ws = FakeWebSocket()
        user_ws = FakeWebSocket()

        host_task = asyncio.create_task(jam_ws(host_ws, session.id, user_id=host_id))
        host_join = json.loads(await host_ws.sent_queue.get())
        assert host_join["type"] == "joined" and host_join["user_id"] == host_id

        user_task = asyncio.create_task(jam_ws(user_ws, session.id, user_id=user_id))
        msg_host = json.loads(await host_ws.sent_queue.get())
        msg_user = json.loads(await user_ws.sent_queue.get())
        assert msg_host["type"] == "joined" and msg_host["user_id"] == user_id
        assert msg_user["type"] == "joined" and msg_user["user_id"] == user_id

        user_ws.queue(
            json.dumps(
                {"op": "start_stream", "stream_id": "s1", "codec": "opus", "premium": True}
            )
        )
        stream_msg = json.loads(await host_ws.sent_queue.get())
        assert stream_msg["type"] == "stream_started"
        assert stream_msg["user_id"] == user_id
        assert stream_msg["stream"]["stream_id"] == "s1"

        host_task.cancel()
        user_task.cancel()
        with suppress(asyncio.CancelledError):
            await host_task
        with suppress(asyncio.CancelledError):
            await user_task

        assert jam_service.economy.get_balance(host_id) == 400
        assert jam_service.economy.get_balance(user_id) == 475

    asyncio.run(run())
