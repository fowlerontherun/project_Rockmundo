from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class DialogueMessage(BaseModel):
    """Represents a single message in a dialogue."""

    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistory(BaseModel):
    """Container storing ordered dialogue messages."""

    messages: List[DialogueMessage] = Field(default_factory=list)

    def add(self, role: str, content: str) -> DialogueMessage:
        msg = DialogueMessage(role=role, content=content)
        self.messages.append(msg)
        return msg
