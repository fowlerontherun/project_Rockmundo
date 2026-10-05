from pathlib import Path
import ast

def test_luthiery_admin_routes_compile_and_mutations_are_audited():
 source=Path("routes/admin_luthiery_routes.py").read_text();ast.parse(source)
 assert "\\nfrom services" not in source
 for action in ("catalogue_enabled","catalogue_update","quality_weights","trait","feature"):
  assert f'"{action}"' in source
 assert '@router.get("/audit")' in source

def test_catalogue_admin_update_exists_and_upserts_unlock():
 source=Path("services/luthiery_catalogue_service.py").read_text();ast.parse(source)
 assert "def admin_update(" in source and "def admin_get(" in source
 assert "ON CONFLICT(content_key) DO UPDATE SET required_level" in source

def test_admin_ui_shows_audit_history():
 source=Path("frontend/src/admin/luthiery/LuthieryTestBench.tsx").read_text()
 assert "/admin/luthiery/audit?limit=50" in source
 assert "Recent Luthiery admin changes" in source
