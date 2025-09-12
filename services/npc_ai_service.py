from __future__ import annotations

import random
from typing import Dict, List, Optional

from backend.models.npc import NPC


class NPCAIService:
    """Generate daily behaviors for NPCs based on their goals and routines."""

    def generate_daily_behavior(
        self, npc: NPC, lifestyle: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        events: List[Dict[str, str]] = []
        lifestyle = lifestyle or {}

        if npc.goals.get("gig") and random.random() < 0.3:
            events.append(
                {
                    "type": "gig",
                    "npc_id": npc.id,
                    "location": npc.routine.get("preferred_venue", "local club"),
                }
            )
        if npc.goals.get("release") and random.random() < 0.1:
            events.append(
                {
                    "type": "release",
                    "npc_id": npc.id,
                    "title": f"New single from {npc.identity}",
                }
            )
        if npc.interaction_hooks and random.random() < 0.2:
            hook, response = random.choice(list(npc.interaction_hooks.items()))
            events.append(
                {
                    "type": "interaction",
                    "npc_id": npc.id,
                    "hook": hook,
                    "response": response,
                }
            )
        return events


npc_ai_service = NPCAIService()
