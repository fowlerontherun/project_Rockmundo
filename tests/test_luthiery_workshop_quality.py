from pathlib import Path
import sqlite3,ast

def test_workshop_schema_is_idempotent(tmp_path):
 sql=Path("migrations/sql/177_luthiery_workshop_quality.sql").read_text();db=tmp_path/"x.db"
 with sqlite3.connect(db) as c:c.executescript(sql);c.executescript(sql)
 assert "character_luthiery_workshops" in {x[0] for x in sqlite3.connect(db).execute("SELECT name FROM sqlite_master WHERE type='table'")}

def test_live_crafting_uses_server_workshop_quality():
 source=Path("routes/luthiery_routes.py").read_text();ast.parse(source)
 craft=source[source.index("def craft_instrument"):source.index('@router.get("/crafted/{item_id}")')]
 assert "workshop_score=luthiery_workshop_service.quality(character_id)" in craft
 model=source[source.index("class CraftInstrument"):source.index("def _authoritative_crafting_skills")]
 assert "workshop_score:" not in model

def test_workshop_upgrade_is_economy_backed():
 source=Path("services/luthiery_workshop_service.py").read_text();ast.parse(source)
 assert "UPGRADE_QUALITIES=(50,60,70,80,90,100)" in source
 assert "luthiery_workshop_upgrade" in source
 assert "ledger_entries" in source
