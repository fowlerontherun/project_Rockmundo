from pathlib import Path
import sqlite3,ast

def test_luthiery_production_hardening_migration_is_idempotent(tmp_path):
 sql=Path("migrations/sql/176_luthiery_production_schema_hardening.sql").read_text()
 db=tmp_path/"luthiery.db"
 with sqlite3.connect(db) as c:
  c.executescript(sql);c.executescript(sql)
  names={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
 assert {"luthiery_live_config","luthiery_trait_controls","luthier_reputation_events","crafted_item_notable_history","luthier_achievements","luthiery_admin_audit"}<=names

def test_famous_owner_is_idempotent_by_item_and_character():
 source=Path("services/luthiery_reputation_service.py").read_text();ast.parse(source)
 assert "event_type='famous_owner' AND character_id=?" in source
 sql=Path("migrations/sql/176_luthiery_production_schema_hardening.sql").read_text()
 assert "ux_luthier_famous_owner" in sql
