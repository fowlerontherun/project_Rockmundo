from pathlib import Path

def test_admin_frontend_has_no_conflict_debris_and_exposes_luthiery_bench():
 for path in ("frontend/src/admin/App.tsx","frontend/src/admin/components/Sidebar.tsx"):
  source=Path(path).read_text()
  assert "<<<<<<<" not in source and "=======" not in source and ">>>>>>>" not in source
 app=Path("frontend/src/admin/App.tsx").read_text()
 side=Path("frontend/src/admin/components/Sidebar.tsx").read_text()
 bench=Path("frontend/src/admin/luthiery/LuthieryTestBench.tsx").read_text()
 assert '/admin/luthiery/test' in app and '/admin/luthiery/test' in side
 assert '/admin/luthiery/demo/craft' in bench
 assert 'Run crafting preview' in bench
