from pathlib import Path
import ast

def test_admin_routes_compile_and_rollback_is_explicit_and_audited():
 source=Path("routes/admin_luthiery_routes.py").read_text();ast.parse(source)
 assert "\\nfrom services" not in source
 assert '@router.post("/audit/{event_id}/rollback")' in source
 assert "Rollback requires explicit confirmation" in source
 assert '_audit(_admin_id,"rollback"' in source
 for action in ("feature","trait","quality_weights","catalogue_update","catalogue_enabled"):
  assert f'action=="{action}"' in source or f'action in ("catalogue_update","catalogue_enabled")' in source

def test_admin_ui_requires_confirmation_before_restore():
 source=Path("frontend/src/admin/luthiery/LuthieryTestBench.tsx").read_text()
 assert "window.confirm(" in source
 assert "/rollback" in source
 assert ">Restore</button>" in source
