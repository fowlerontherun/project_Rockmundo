from pathlib import Path
import ast

def test_luthiery_production_python_sources_compile_and_have_no_literal_newline_corruption():
 for path in ("routes/admin_luthiery_routes.py","services/luthiery_crafting_service.py"):
  source=Path(path).read_text()
  assert "\\\\nfrom services" not in source
  ast.parse(source)

def test_admin_demo_route_is_dry_run_only():
 source=Path("services/luthiery_crafting_service.py").read_text()
 start=source.index("def admin_preview")
 end=source.index("def craft(",start)
 preview=source[start:end]
 assert '"dry_run":True' in preview
 assert "INSERT INTO crafted_items" not in preview
 assert "UPDATE character_crafting_materials" not in preview
