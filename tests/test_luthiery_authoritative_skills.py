from pathlib import Path
import ast

def test_public_luthiery_route_uses_server_authoritative_skills():
 source=Path("routes/luthiery_routes.py").read_text();ast.parse(source)
 assert "def _authoritative_crafting_skills" in source
 assert "CRAFTING_SKILL_NAMES=" in source
 craft=source[source.index("def craft_instrument"):source.index('@router.get("/crafted/{item_id}")')]
 assert "skills=_authoritative_crafting_skills(character_id)" in craft
 assert "skills=skills" in craft
 assert "skill_names =" not in craft

def test_client_craft_payload_has_no_skill_or_workshop_authority():
 source=Path("routes/luthiery_routes.py").read_text()
 model=source[source.index("class CraftInstrument"):source.index("def _authoritative_crafting_skills")]
 assert "skills:" not in model
 assert "workshop_score:" not in model

def test_catalogue_exposes_all_authoritative_crafting_skill_levels():
 source=Path("routes/luthiery_routes.py").read_text()
 catalogue=source[source.index("def catalogue("):source.index('@router.get("/materials/inventory")')]
 assert 'data["skill_levels"] = skills' in catalogue
