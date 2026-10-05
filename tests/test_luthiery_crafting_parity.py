from pathlib import Path
import ast

def test_live_and_preview_share_quality_calculation_and_recipe_validation():
 source=Path("services/luthiery_crafting_service.py").read_text();ast.parse(source)
 assert "\\nfrom services" not in source
 assert source.count("self._quality_result(")>=2
 assert source.count("self._validate_recipe_choice(")>=2
 craft=source[source.index("    def craft("):source.index("    def rework(")]
 assert "level * .35 + material_score * .35" not in craft
 assert "balance_service.quality_weights()" in source

def test_preview_enforces_production_recipe_rules():
 source=Path("services/luthiery_crafting_service.py").read_text()
 preview=source[source.index("    def admin_preview("):source.index("    def craft(")]
 assert "Exactly body, neck, fretboard, electronics and hardware are required" in preview
 assert "Instrument Finishing level" in preview
 shared=source[source.index("    def _validate_recipe_choice"):source.index("    def admin_preview(")]
 assert "instrument_compatibility_json" in shared
 assert "MATERIAL_TYPES_BY_PART" in shared
