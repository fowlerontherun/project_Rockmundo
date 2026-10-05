from pathlib import Path
import ast

def test_batch_simulator_is_bounded_and_read_only():
 source=Path("routes/admin_luthiery_routes.py").read_text()
 ast.parse(source)
 start=source.index('def demo_batch')
 batch=source[start:]
 assert 'payload.samples>1000' in batch
 assert 'admin_preview' in batch
 assert 'INSERT INTO crafted_items' not in batch
 assert 'UPDATE character_crafting_materials' not in batch

def test_admin_test_bench_exposes_batch_distribution():
 source=Path("frontend/src/admin/luthiery/LuthieryTestBench.tsx").read_text()
 assert '/admin/luthiery/demo/batch' in source
 assert 'Simulate batch' in source
 assert 'Tier distribution' in source
 assert 'Trait frequency' in source
