from pathlib import Path
import ast

def test_craft_revalidates_mutable_catalogue_after_write_lock():
 source=Path("services/luthiery_crafting_service.py").read_text();ast.parse(source)
 craft=source[source.index("    def craft("):source.index("    def rework(")]
 locked=craft[craft.index('conn.execute("BEGIN IMMEDIATE")'):]
 assert "Shape availability changed during crafting" in locked
 assert "material availability changed during crafting" in locked
 assert "component availability changed during crafting" in locked
 assert "SELECT * FROM instrument_shapes" in locked
 assert "SELECT * FROM crafting_materials" in locked
 assert "SELECT * FROM crafting_component_designs" in locked

def test_commit_time_feature_policy_uses_same_connection():
 source=Path("services/luthiery_crafting_service.py").read_text()
 craft=source[source.index("    def craft("):source.index("    def rework(")]
 locked=craft[craft.index('conn.execute("BEGIN IMMEDIATE")'):]
 assert "SELECT key,value_json FROM luthiery_live_config" in locked
 assert "current_features" in locked
 assert "_validate_advanced_features(current_shape,resolved,finish_key,current_features)" in locked
 assert "balance_service." not in locked

def test_profile_calculation_remains_outside_write_lock():
 source=Path("services/luthiery_crafting_service.py").read_text()
 craft=source[source.index("    def craft("):source.index("    def rework(")]
 assert craft.index("profile = build_profile") < craft.index('conn.execute("BEGIN IMMEDIATE")')
