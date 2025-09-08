from __future__ import annotations

import random
from typing import Dict, List, Optional

from backend.models.npc import NPC
from backend.models.npc_dialogue import DialogueTree


# Simple seasonal event definitions used by ``generate_seasonal_event``.
# Each season maps to a list of potential events with stat effects.  The
# structure is intentionally lightweight to keep the service usable in unit
# tests without any external data files.
SEASONAL_EVENTS: Dict[str, List[Dict]] = {
    "summer": [
        {"name": "summer_festival", "effects": {"fame": 5}},
        {"name": "tourist_rush", "effects": {"fame": 3}},
    ],
    "winter": [
        {"name": "snowstorm", "effects": {"activity": -2}},
        {"name": "cold_snap", "effects": {"activity": -1}},
    ],
}


class _InMemoryNPCDB:
    """Very small in-memory storage used for tests and local use."""

    def __init__(self):
        self._npcs: Dict[int, NPC] = {}
        self._next_id = 1

    def add(self, npc: NPC) -> NPC:
        npc.id = self._next_id
        self._npcs[self._next_id] = npc
        self._next_id += 1
        return npc

    def get(self, npc_id: int) -> Optional[NPC]:
        return self._npcs.get(npc_id)

    def delete(self, npc_id: int) -> bool:
        return self._npcs.pop(npc_id, None) is not None

    def all(self):
        return list(self._npcs.values())


class NPCService:
    """Service providing CRUD operations and simple stat simulations for NPCs."""

    def __init__(self, db: Optional[_InMemoryNPCDB] = None):
        self.db = db or _InMemoryNPCDB()

    # ---- CRUD ------------------------------------------------------------
    def create_npc(
        self,
        identity: str,
        npc_type: str,
        dialogue_hooks=None,
        stats=None,
        goals=None,
        routine=None,
        interaction_hooks=None,
    ) -> Dict:
        npc = NPC(
            id=None,
            identity=identity,
            npc_type=npc_type,
            dialogue_hooks=dialogue_hooks or {},
            interaction_hooks=interaction_hooks or {},
            goals=goals or {},
            routine=routine or {},
            stats=stats or {},
        )
        self.db.add(npc)
        return npc.to_dict()

    def get_npc(self, npc_id: int) -> Optional[Dict]:
        npc = self.db.get(npc_id)
        return npc.to_dict() if npc else None

    def update_npc(self, npc_id: int, **updates) -> Optional[Dict]:
        npc = self.db.get(npc_id)
        if not npc:
            return None
        if 'identity' in updates:
            npc.identity = updates['identity']
        if 'npc_type' in updates:
            npc.npc_type = updates['npc_type']
        if 'dialogue_hooks' in updates and updates['dialogue_hooks'] is not None:
            npc.dialogue_hooks = updates['dialogue_hooks']
        if 'interaction_hooks' in updates and updates['interaction_hooks'] is not None:
            npc.interaction_hooks = updates['interaction_hooks']
        if 'goals' in updates and updates['goals'] is not None:
            npc.goals = updates['goals']
        if 'routine' in updates and updates['routine'] is not None:
            npc.routine = updates['routine']
        if 'stats' in updates and updates['stats'] is not None:
            npc.stats = updates['stats']
        return npc.to_dict()

    def delete_npc(self, npc_id: int) -> bool:
        return self.db.delete(npc_id)

    # ---- Dialogue --------------------------------------------------------
    def edit_dialogue(self, npc_id: int, dialogue: Dict) -> Optional[Dict]:
        """Replace the dialogue tree for ``npc_id`` with ``dialogue``."""

        npc = self.db.get(npc_id)
        if not npc:
            return None
        tree = DialogueTree(**dialogue)
        npc.dialogue_hooks = tree.dict()
        return npc.dialogue_hooks

    def preview_dialogue(self, npc_id: int, choices: List[int]) -> Optional[List[str]]:
        """Traverse the dialogue tree following ``choices`` and return lines."""

        npc = self.db.get(npc_id)
        if not npc or not npc.dialogue_hooks:
            return None
        tree = DialogueTree(**npc.dialogue_hooks)
        return tree.traverse(choices)

    # ---- Events ----------------------------------------------------------
    def generate_seasonal_event(self, npc_id: int, season: str | None = None) -> Optional[Dict]:
        """Generate and apply a seasonal event to ``npc_id``.

        A season (e.g. ``"summer"`` or ``"winter"``) may be provided
        explicitly.  If omitted a random season is chosen.  The selected
        event's stat effects are applied directly to the NPC and the full
        event payload is returned.
        """

        npc = self.db.get(npc_id)
        if not npc:
            return None

        # Choose a season and a random event within that season
        season = (season or random.choice(list(SEASONAL_EVENTS.keys()))).lower()
        events = SEASONAL_EVENTS.get(season)
        if not events:
            return None
        event = random.choice(events)
        effects = event.get("effects", {})

        # Apply effects to the NPC stats
        for stat, delta in effects.items():
            npc.stats[stat] = npc.stats.get(stat, 0) + delta

        return {
            "id": npc.id,
            "season": season,
            "event": event.get("name", ""),
            "effects": effects,
            "stats": npc.stats,
        }

    # ---- Simulation ------------------------------------------------------
    def preview_npc(
        self,
        identity: str,
        npc_type: str,
        dialogue_hooks=None,
        stats=None,
        goals=None,
        routine=None,
        interaction_hooks=None,
    ) -> Dict:
        """Simulate NPC stats without persisting to the DB."""
        npc = NPC(
            id=None,
            identity=identity,
            npc_type=npc_type,
            dialogue_hooks=dialogue_hooks or {},
            interaction_hooks=interaction_hooks or {},
            goals=goals or {},
            routine=routine or {},
            stats=stats or {},
        )
        fame_gain = random.randint(0, npc.stats.get('activity', 5))
        npc.stats['fame'] = npc.stats.get('fame', 0) + fame_gain
        return {"fame_gain": fame_gain, "stats": npc.stats}

    def simulate_npc(self, npc_id: int) -> Optional[Dict]:
        npc = self.db.get(npc_id)
        if not npc:
            return None
        fame_gain = random.randint(0, npc.stats.get('activity', 5))
        npc.stats['fame'] = npc.stats.get('fame', 0) + fame_gain
        return {"id": npc.id, "fame_gain": fame_gain, "stats": npc.stats}

    def simulate_all(self):
        for npc in self.db.all():
            self.simulate_npc(npc.id)


npc_service = NPCService()

__all__ = ["NPCService", "npc_service"]
