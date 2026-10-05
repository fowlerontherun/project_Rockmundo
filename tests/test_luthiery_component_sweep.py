from pathlib import Path
import ast

def test_component_sweep_is_bounded_and_part_scoped():
 source=Path("routes/admin_luthiery_routes.py").read_text();ast.parse(source)
 start=source.index('def demo_component_sweep');body=source[start:]
 assert 'samples=min(max(payload.samples,1),250)' in body
 assert 'candidate[part_type]["component_key"]=component["key"]' in body
 assert 'spread<1' in body and 'spread>12' in body
 assert 'INSERT INTO crafted_items' not in body

def test_testbench_exposes_component_comparison():
 source=Path("frontend/src/admin/luthiery/LuthieryTestBench.tsx").read_text()
 assert '/admin/luthiery/demo/component-sweep/' in source
 assert 'Compare components' in source
 assert 'Component part' in source
