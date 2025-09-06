"""Service layer for item crafting using recipes."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

from services.item_service import item_service


@dataclass
class Recipe:
    """Recipe definition for crafting.

    Attributes:
        name: Unique recipe name.
        result_item_id: Item created when crafting succeeds.
        components: Mapping of required item_id to quantity.
    """

    name: str
    result_item_id: int
    components: Dict[int, int]


class CraftingService:
    """Manage crafting recipes and consume inventory items."""

    def __init__(self) -> None:
        self._recipes: Dict[str, Recipe] = {}

    # ------------------------------------------------------------------
    # Recipe management
    # ------------------------------------------------------------------
    def add_recipe(self, recipe: Recipe) -> None:
        self._recipes[recipe.name] = recipe

    def get_recipe(self, name: str) -> Recipe:
        recipe = self._recipes.get(name)
        if not recipe:
            raise ValueError("recipe not found")
        return recipe

    def list_recipes(self) -> List[Recipe]:
        return list(self._recipes.values())

    # ------------------------------------------------------------------
    # Crafting operations
    # ------------------------------------------------------------------
    def craft(self, user_id: int, recipe_name: str) -> None:
        recipe = self.get_recipe(recipe_name)
        inventory = item_service.get_inventory(user_id)
        for item_id, qty in recipe.components.items():
            if inventory.get(item_id, 0) < qty:
                raise ValueError("missing components")
        for item_id, qty in recipe.components.items():
            item_service.remove_from_inventory(user_id, item_id, qty)
        item_service.add_to_inventory(user_id, recipe.result_item_id, 1)

    # helper for routes
    def asdict(self, recipe: Recipe) -> Dict:
        return asdict(recipe)


crafting_service = CraftingService()

__all__ = ["CraftingService", "crafting_service", "Recipe"]
