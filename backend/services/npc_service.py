from __future__ import annotations

import random
from typing import Dict, Optional

from models.npc import NPC


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
    def create_npc(self, identity: str, npc_type: str, dialogue_hooks=None, stats=None) -> Dict:
        npc = NPC(
            id=None,
            identity=identity,
            npc_type=npc_type,
            dialogue_hooks=dialogue_hooks or {},
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
        if 'stats' in updates and updates['stats'] is not None:
            npc.stats = updates['stats']
        return npc.to_dict()

    def delete_npc(self, npc_id: int) -> bool:
        return self.db.delete(npc_id)

    # ---- Simulation ------------------------------------------------------
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
