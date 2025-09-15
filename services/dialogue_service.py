"""Service layer for NPC/user dialogue via an LLM provider."""
from __future__ import annotations

from typing import List, Optional, Protocol


from models.dialogue import DialogueMessage
from backend.services.moderation_service import moderate_content
from backend.models.dialogue import DialogueMessage
from services.moderation_service import moderate_content



class LLMProvider(Protocol):
    async def complete(self, history: List[DialogueMessage]) -> str: ...


class EchoLLM:
    """Fallback LLM provider that echoes the last user message."""

    async def complete(self, history: List[DialogueMessage]) -> str:  # pragma: no cover - trivial
        if history:
            return f"Echo: {history[-1].content}"
        return "..."


class DialogueService:
    """High level interface managing conversation state and generation."""

    def __init__(self, llm_client: Optional[LLMProvider] = None) -> None:
        self.llm = llm_client or EchoLLM()

    async def generate_reply(self, history: List[DialogueMessage]) -> DialogueMessage:
        raw = await self.llm.complete(history)
        filtered = moderate_content(raw)
        return DialogueMessage(role="npc", content=filtered)
