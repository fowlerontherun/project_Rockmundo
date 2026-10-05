import json, sqlite3
from services.crafted_instrument_effects_service import CraftedInstrumentEffectsService

def db(tmp_path):
 p=str(tmp_path/"x.db")
 with sqlite3.connect(p) as c:
  c.execute("""CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,
  stat_modifiers_json TEXT,condition_percent INTEGER)""")
  c.execute("INSERT INTO crafted_items VALUES (1,10,?,100)",(json.dumps({"performance_quality":.08,"stage_presence":.08,"recording_quality":.07}),))
  c.execute("INSERT INTO crafted_items VALUES (2,20,?,50)",(json.dumps({"performance_quality":.08,"stage_presence":.08}),))
 return p

def test_owner_required_and_context_capped(tmp_path):
 s=CraftedInstrumentEffectsService(db(tmp_path))
 assert s.item_effects(99,1,"performance")==0
 assert s.item_effects(10,1,"performance")==.12

def test_condition_scales_effect(tmp_path):
 s=CraftedInstrumentEffectsService(db(tmp_path))
 assert s.item_effects(20,2,"performance")==.08

def test_equipped_aggregation_is_capped_and_explicit(tmp_path):
 s=CraftedInstrumentEffectsService(db(tmp_path))
 assert s.equipped_effects({10:1,20:2},"performance")==.12
 assert s.equipped_effects({},"performance")==0

def test_missing_phase_tables_are_backward_compatible(tmp_path):
 s=CraftedInstrumentEffectsService(str(tmp_path/"empty.db"))
 assert s.item_effects(1,1,"rehearsal")==0
