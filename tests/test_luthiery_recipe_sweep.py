from pathlib import Path
import ast

def test_recipe_sweep_is_bounded_and_changes_only_body_material():
 source=Path("routes/admin_luthiery_routes.py").read_text();ast.parse(source)
 start=source.index('def demo_recipe_sweep');body=source[start:]
 assert 'samples=min(max(payload.samples,1),250)' in body
 assert 'candidate["body"]["material_key"]=material["key"]' in body
 assert 'spread<2' in body and 'spread>20' in body
 assert 'INSERT INTO crafted_items' not in body

def test_testbench_exposes_body_material_comparison():
 source=Path("frontend/src/admin/luthiery/LuthieryTestBench.tsx").read_text()
 assert '/admin/luthiery/demo/recipe-sweep' in source
 assert 'Compare body materials' in source
 assert 'Body material comparison' in source
