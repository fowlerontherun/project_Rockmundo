from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from backend.models.npc_dialogue import DialogueNode, DialogueResponse, DialogueTree
from backend.services.npc_service import NPCService


class ShopNPCService:
    """Simple helper around :class:`NPCService` for shop interactions.

    It provides dialogue traversal for a pre-created shop keeper NPC and a
    daily rotating promotion that acts as the shop's "daily special".
    The goal is not to be production ready but to supply enough behaviour for
    tests and the demo front end.
    """

    def __init__(self, npc_service: Optional[NPCService] = None):
        self._npc_service = npc_service or NPCService()
        # create a default shop NPC with a tiny dialogue tree
        dialogue = self._default_dialogue().dict()
        npc = self._npc_service.create_npc("Shopkeeper", "merchant", dialogue_hooks=dialogue)
        self._npc_id = npc["id"]
        # rotating promotions
        self._promotions: List[Dict[str, str]] = [
            {"item": "Guitar Strings", "description": "10% off all strings today!"},
            {"item": "Vinyl Cleaner", "description": "Buy one get one free."},
            {"item": "Tour Poster", "description": "Limited edition poster available."},
        ]

    # ------------------------------------------------------------------
    def _default_dialogue(self) -> DialogueTree:
        """Return a tiny dialogue tree used for the shop keeper."""

        return DialogueTree(
            root="start",
            nodes={
                "start": DialogueNode(
                    id="start",
                    text="Welcome to the shop!",
                    responses=[
                        DialogueResponse(text="What's today's special?", next_id="special"),
                        DialogueResponse(text="Just browsing.", next_id="end"),
                    ],
                ),
                "special": DialogueNode(
                    id="special",
                    text="Check out our daily deal!",
                    responses=[DialogueResponse(text="Thanks!", next_id="end")],
                ),
                "end": DialogueNode(id="end", text="Come back soon!"),
            },
        )

    # ------------------------------------------------------------------
    def get_dialogue(self, choices: Optional[List[int]] = None) -> Dict[str, List[str]]:
        """Return dialogue lines and response options following ``choices``.

        Args:
            choices: optional sequence of response indices indicating the path
                taken through the dialogue tree.

        Returns:
            Dict containing ``lines`` encountered so far and the available
            ``options`` for the next step. If the dialogue has ended the
            options list will be empty.
        """

        choices = choices or []
        npc = self._npc_service.db.get(self._npc_id)
        if not npc or not npc.dialogue_hooks:
            return {"lines": [], "options": []}
        tree = DialogueTree(**npc.dialogue_hooks)
        lines = tree.traverse(choices)

        # determine current node after choices to expose available responses
        current = tree.nodes.get(tree.root)
        for idx in choices:
            if not current or idx < 0 or idx >= len(current.responses):
                current = None
                break
            resp = current.responses[idx]
            if not resp.next_id:
                current = None
                break
            current = tree.nodes.get(resp.next_id)

        options: List[str] = []
        if current:
            options = [resp.text for resp in current.responses]
        return {"lines": lines, "options": options}

    # ------------------------------------------------------------------
    def get_daily_special(self) -> Dict[str, str]:
        """Return the promotion for the current day.

        The promotion rotates based on the current day so that tests can
        rely on deterministic results without needing persistent storage.
        """

        idx = date.today().toordinal() % len(self._promotions)
        return self._promotions[idx]


# default singleton used by routes
shop_npc_service = ShopNPCService()

__all__ = ["shop_npc_service", "ShopNPCService"]
