from pathlib import Path
import ast

def test_advanced_feature_validation_is_shared_by_preview_and_live_craft():
 source=Path("services/luthiery_crafting_service.py").read_text();ast.parse(source)
 assert source.count("self._validate_advanced_features(shape,resolved,finish_key)")>=2
 assert 'component["key"]=="luthier.component.electronics.boutique"' in source
 assert 'feature_enabled("boutique_electronics")' in source
 assert 'feature_enabled("premium_materials")' in source
 assert 'feature_enabled("legendary_shapes")' in source
 assert 'feature_enabled("metallic_finishes")' in source
 assert "\\nfrom services" not in source

def test_admin_bench_exposes_live_advanced_gates():
 source=Path("frontend/src/admin/luthiery/LuthieryTestBench.tsx").read_text()
 assert "/admin/luthiery/features" in source
 assert "Advanced content gates" in source
 assert "live server-side gates" in source
