import json,sqlite3
from services.crafted_instrument_effects_service import CraftedInstrumentEffectsService

def test_single_crafted_instrument_cannot_fill_whole_band_cap(tmp_path):
 p=str(tmp_path/"effects.db")
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,stat_modifiers_json TEXT,condition_percent INTEGER)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,?,100)",(json.dumps({"performance_quality":.1,"stage_presence":.1,"audience_reaction":.1}),))
 svc=CraftedInstrumentEffectsService(p)
 assert svc.item_effects(10,1,"performance")==.08

def test_condition_still_scales_balanced_cap(tmp_path):
 p=str(tmp_path/"effects.db")
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,stat_modifiers_json TEXT,condition_percent INTEGER)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,?,50)",(json.dumps({"performance_quality":.1,"stage_presence":.1}),))
 assert CraftedInstrumentEffectsService(p).item_effects(10,1,"performance")==.04
