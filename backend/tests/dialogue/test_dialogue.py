import asyncio

import pytest

import realtime.dialogue_gateway as dialogue_gateway
from backend.models.dialogue import DialogueMessage
from realtime.dialogue_gateway import router as dialogue_router
from backend.services.dialogue_service import DialogueService
from fastapi import FastAPI
from fastapi.testclient import TestClient


class EchoLLM:
    async def complete(self, history):
        return f"NPC says: {history[-1].content}"


class BadLLM:
    async def complete(self, history):
        return "Violence is never the answer"


def test_service_moderates_response():
    service = DialogueService(llm_client=BadLLM())
    history = [DialogueMessage(role="user", content="hello")]
    reply = asyncio.get_event_loop().run_until_complete(service.generate_reply(history))
    assert "violence" not in reply.content.lower()
    assert reply.role == "npc"


@pytest.mark.skipif(not hasattr(TestClient, "websocket_connect"), reason="websocket support not available")
def test_dialogue_websocket_flow(monkeypatch):
    app = FastAPI()
    app.include_router(dialogue_router)
    service = DialogueService(llm_client=EchoLLM())
    monkeypatch.setattr(dialogue_gateway, "DialogueService", lambda: service)
    client = TestClient(app)
    with client.websocket_connect("/dialogue/ws/42", headers={"X-User-Id": "5"}) as ws:
        ws.send_text("hi there")
        resp = ws.receive_text()
        assert "hi there" in resp.lower()
