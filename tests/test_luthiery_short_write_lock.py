from pathlib import Path
import ast

def test_craft_write_lock_starts_after_profile_calculation():
 source=Path("services/luthiery_crafting_service.py").read_text();ast.parse(source)
 craft=source[source.index("    def craft("):source.index("    def rework(")]
 lock=craft.index('conn.execute("BEGIN IMMEDIATE")')
 assert craft.index("profile = build_profile") < lock
 assert craft.index("self._validate_advanced_features") < lock
 assert craft.index("score = self._quality_result") < lock

def test_craft_rechecks_idempotency_and_inventory_after_write_lock():
 source=Path("services/luthiery_crafting_service.py").read_text()
 craft=source[source.index("    def craft("):source.index("    def rework(")]
 locked=craft[craft.index('conn.execute("BEGIN IMMEDIATE")'):]
 assert "SELECT crafted_item_id FROM crafting_jobs" in locked
 assert "SELECT quantity FROM character_crafting_materials" in locked
 assert "quantity=quantity-1" in locked
 assert "INSERT INTO crafted_items" in locked
 assert "INSERT INTO crafted_item_events" in locked

def test_no_balance_or_profile_helpers_inside_write_lock():
 source=Path("services/luthiery_crafting_service.py").read_text()
 craft=source[source.index("    def craft("):source.index("    def rework(")]
 locked=craft[craft.index('conn.execute("BEGIN IMMEDIATE")'):]
 assert "balance_service." not in locked
 assert "build_profile(" not in locked
 assert "_quality_result(" not in locked
