import json,sqlite3,pytest
from services.crafted_instrument_equipment_service import CraftedInstrumentEquipmentService
from services.crafted_instrument_effects_service import CraftedInstrumentEffectsService

def setup(tmp_path):
 p=str(tmp_path/"eq.db")
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,instrument_type TEXT,name TEXT,serial_number TEXT,stat_modifiers_json TEXT,condition_percent INTEGER)")
  c.execute("CREATE TABLE band_members(band_id INTEGER,character_id INTEGER,role TEXT)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,'guitar','G','S1',?,100)",(json.dumps({"performance_quality":.08,"stage_presence":.08,"practice_effectiveness":.06}),))
  c.execute("INSERT INTO crafted_items VALUES(2,20,'bass','B','S2',?,100)",(json.dumps({"performance_quality":.08,"stage_presence":.08,"practice_effectiveness":.06}),))
  c.executemany("INSERT INTO band_members VALUES(1,?,?)",[(10,"lead guitar"),(20,"bass")])
 return p

def test_equipment_is_owner_safe_role_compatible_and_one_per_character(tmp_path):
 p=setup(tmp_path);s=CraftedInstrumentEquipmentService(p)
 with pytest.raises(ValueError):s.equip(99,1,"lead guitar")
 with pytest.raises(ValueError):s.equip(10,1,"bass")
 assert s.equip(10,1,"lead guitar")["id"]==1
 assert s.equipped(10)["id"]==1
 s.unequip(10);assert s.equipped(10) is None

def test_band_effects_use_only_explicit_equipment_and_cap_stacking(tmp_path):
 p=setup(tmp_path);eq=CraftedInstrumentEquipmentService(p);fx=CraftedInstrumentEffectsService(p)
 assert fx.band_effects(1,"performance")==0
 eq.equip(10,1,"lead guitar");eq.equip(20,2,"bass")
 assert fx.band_effects(1,"performance")==.12
