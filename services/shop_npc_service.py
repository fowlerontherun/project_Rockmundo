from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional


from models.npc_dialogue import DialogueNode, DialogueResponse, DialogueTree
from backend.services.npc_service import NPCService
from backend.services.city_shop_service import CityShopService, city_shop_service
from backend.services.item_service import item_service as default_item_service, ItemService


class ShopNPCService:
    """Simple helper around :class:`NPCService` for shop interactions.

    It provides dialogue traversal for a pre-created shop keeper NPC and a
    daily rotating promotion that acts as the shop's "daily special".
    The goal is not to be production ready but to supply enough behaviour for
    tests and the demo front end.
    """

    def __init__(
        self,
        npc_service: Optional[NPCService] = None,
        shop_service: Optional[CityShopService] = None,
        item_service: Optional[ItemService] = None,
    ):
        self._npc_service = npc_service or NPCService()
        self._shop_service = shop_service or city_shop_service
        self._item_service = item_service or default_item_service
        # create a default shop NPC with a tiny dialogue tree
        tree = self._default_dialogue()
        dialogue = tree.dict()
        npc = self._npc_service.create_npc("Shopkeeper", "merchant", dialogue_hooks=dialogue)
        self._npc_id = npc["id"]
        self._dialogue_tree = tree
        # add a simple drug dealer NPC
        dealer_tree = self._dealer_dialogue()
        dealer = self._npc_service.create_npc("Dealer", "merchant", dialogue_hooks=dealer_tree.dict())
        self._dealer_id = dealer["id"]
        self._dealer_tree = dealer_tree
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
                        DialogueResponse(text="Can we negotiate?", next_id="haggle"),
                    ],
                ),
                "special": DialogueNode(
                    id="special",
                    text="Check out our daily deal!",
                    responses=[DialogueResponse(text="Thanks!", next_id="end")],
                ),
                "haggle": DialogueNode(
                    id="haggle",
                    text="Think you can beat my price? Make me an offer.",
                    responses=[DialogueResponse(text="Maybe next time", next_id="end")],
                ),
                "haggle_success": DialogueNode(
                    id="haggle_success",
                    text="Alright, you've got yourself a deal!",
                    responses=[DialogueResponse(text="Thanks!", next_id="end")],
                ),
                "haggle_fail": DialogueNode(
                    id="haggle_fail",
                    text="Nice try, but the price stands.",
                    responses=[DialogueResponse(text="Fair enough", next_id="end")],
                ),
                "end": DialogueNode(id="end", text="Come back soon!"),
            },
        )

    def _dealer_dialogue(self) -> DialogueTree:
        return DialogueTree(
            root="start",
            nodes={
                "start": DialogueNode(
                    id="start",
                    text="Looking for something... special?",
                    responses=[
                        DialogueResponse(text="What do you have?", next_id="end"),
                        DialogueResponse(text="No thanks.", next_id="end"),
                    ],
                ),
                "end": DialogueNode(id="end", text="Stay safe out there."),
            },
        )

    def _run_dialogue(
        self, npc_id: int, tree: DialogueTree, choices: Optional[List[int]]
    ) -> Dict[str, List[str]]:
        choices = choices or []
        npc = self._npc_service.db.get(npc_id)
        if not npc or not npc.dialogue_hooks:
            return {"lines": [], "options": []}
        lines = tree.traverse(choices)
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
    def get_dialogue(self, choices: Optional[List[int]] = None) -> Dict[str, List[str]]:
        """Return dialogue lines and response options for the shop keeper."""

        return self._run_dialogue(self._npc_id, self._dialogue_tree, choices)

    def get_dealer_dialogue(
        self, choices: Optional[List[int]] = None
    ) -> Dict[str, List[str]]:
        """Return dialogue lines and options for the drug dealer NPC."""

        return self._run_dialogue(self._dealer_id, self._dealer_tree, choices)

    def list_drug_offers(self, shop_id: int) -> List[Dict[str, int]]:
        """Expose available drug items in a shop."""

        return self._shop_service.list_drugs(shop_id)

    def purchase_drug(
        self, shop_id: int, user_id: int, drug_id: int, quantity: int = 1
    ) -> int:
        """Delegate purchase of a drug item enforcing simple restrictions."""

        item = self._item_service.get_item(drug_id)
        if item.category != "drug":
            raise ValueError("not a drug")
        addiction = float(item.stats.get("addiction_rate", 0))
        if addiction > 0.5 and quantity > 1:
            raise ValueError("purchase limit exceeded")
        return self._shop_service.purchase_drug(shop_id, user_id, drug_id, quantity)

    # ------------------------------------------------------------------
    def get_haggle_dialogue(self, success: bool) -> Dict[str, List[str]]:
        """Return dialogue lines for the result of a negotiation."""

        node_id = "haggle_success" if success else "haggle_fail"
        node = self._dialogue_tree.nodes.get(node_id)
        if not node:
            return {"lines": [], "options": []}
        return {
            "lines": [node.text],
            "options": [resp.text for resp in node.responses],
        }

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
