from pathlib import Path
import ast

def test_luthiery_python_sources_parse():
 for path in ("services/luthiery_crafting_service.py","services/luthiery_stats_service.py","services/luthiery_balance_service.py"):
  ast.parse(Path(path).read_text())

def test_live_craft_snapshots_balance_before_write_lock():
 source=Path("services/luthiery_crafting_service.py").read_text()
 craft=source[source.index("    def craft("):source.index("    def rework(")]
 assert craft.index("live_balance=balance_service.snapshot()") < craft.index('conn.execute("BEGIN IMMEDIATE")')
 locked=craft[craft.index('conn.execute("BEGIN IMMEDIATE")'):]
 assert "balance_service.feature_enabled" not in locked
 assert "balance_service.quality_weights" not in locked
 assert 'live_balance["features"]' in locked
 assert 'live_balance["quality_weights"]' in locked

def test_balance_snapshot_reads_weights_and_features_together():
 source=Path("services/luthiery_balance_service.py").read_text()
 assert "def snapshot(self):" in source
 assert "SELECT key,value_json FROM luthiery_live_config" in source
 assert '"quality_weights"' in source and '"features"' in source
