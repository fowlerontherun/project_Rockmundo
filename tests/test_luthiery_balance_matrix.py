from pathlib import Path
import ast

def test_progression_matrix_is_admin_bounded_and_has_balance_guards():
 source=Path("routes/admin_luthiery_routes.py").read_text();ast.parse(source)
 start=source.index('def demo_matrix');body=source[start:]
 assert 'samples=min(max(payload.samples,1),500)' in body
 assert '"Novice":10' in body and '"Competent":50' in body and '"Master":100' in body
 assert 'Novices produce Masterwork/Legendary' in body
 assert 'Master progression has less than a 10-point' in body
 assert 'INSERT INTO crafted_items' not in body

def test_testbench_exposes_progression_comparison():
 source=Path("frontend/src/admin/luthiery/LuthieryTestBench.tsx").read_text()
 assert '/admin/luthiery/demo/matrix' in source
 assert 'Compare skill progression' in source
 assert 'Balance warnings' in source
