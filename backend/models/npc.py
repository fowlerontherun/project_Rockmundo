from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class NPC:
    """Simple data model representing a non-player character."""

    id: int | None
    identity: str
    npc_type: str
    dialogue_hooks: Dict[str, str] = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "identity": self.identity,
            "npc_type": self.npc_type,
            "dialogue_hooks": dict(self.dialogue_hooks),
            "stats": dict(self.stats),
        }
