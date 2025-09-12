"""Dialogue tree schema for NPC conversations."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DialogueTrigger(BaseModel):
    """Optional trigger fired when a response is chosen."""

    event: str
    params: Dict[str, str] = Field(default_factory=dict)


class DialogueResponse(BaseModel):
    """A possible player response from a dialogue node."""

    text: str
    next_id: Optional[str] = None
    triggers: List[DialogueTrigger] = Field(default_factory=list)


class DialogueNode(BaseModel):
    """A single node within the dialogue tree."""

    id: str
    text: str
    responses: List[DialogueResponse] = Field(default_factory=list)


class DialogueTree(BaseModel):
    """Container describing a full dialogue tree.

    The tree starts at the node referenced by ``root`` and can be traversed by
    selecting response indices.
    """

    root: str
    nodes: Dict[str, DialogueNode] = Field(default_factory=dict)

    def traverse(self, choices: List[int]) -> List[str]:
        """Follow the dialogue tree based on ``choices``.

        Args:
            choices: A list of response indices to select at each step.

        Returns:
            Ordered list of dialogue lines encountered during traversal.
        """

        lines: List[str] = []
        current = self.nodes.get(self.root)
        if not current:
            return lines
        lines.append(current.text)
        for idx in choices:
            if idx < 0 or idx >= len(current.responses):
                break
            resp = current.responses[idx]
            lines.append(resp.text)
            if not resp.next_id:
                break
            next_node = self.nodes.get(resp.next_id)
            if not next_node:
                break
            current = next_node
            lines.append(current.text)
        return lines
