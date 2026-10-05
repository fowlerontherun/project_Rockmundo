import json,sqlite3,pytest
from services.crafted_instrument_equipment_service import CraftedInstrumentEquipmentService
from services.crafted_instrument_effects_service import CraftedInstrumentEffectsService

def setup(tmp_path):
 p=str(tmp_path/"wear.db")
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,instrument_type TEXT,name TEXT,serial_number TEXT,stat_modifiers_json TEXT,condition_percent INTEGER)")
  c.execute("CREATE TABLE band_members(band_id INTEGER,character_id INTEGER,role TEXT)")
  c.execute("CREATE TABLE crafted_item_events(id INTEGER PRIMARY KEY,crafted_item_id INTEGER,character_id INTEGER,event_type TEXT,details_json TEXT)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,'guitar','G','S',?,100)",(json.dumps({"recording_quality":.08,"instrument_effectiveness":.08}),))
  c.execute("INSERT INTO band_members VALUES(1,10,'lead guitar')")
 return p

def test_wear_scales_effect_and_maintenance_restores_condition(tmp_path):
 p=setup(tmp_path);eq=CraftedInstrumentEquipmentService(p);fx=CraftedInstrumentEffectsService(p)
 eq.equip(10,1,"lead guitar")
 before=fx.band_effects(1,"recording")
 assert eq.wear_band(1,20)==1
 after=fx.band_effects(1,"recording")
 assert after<before
 item=eq.repair(10,1,25)
 assert item["condition_percent"]==100

def test_other_character_cannot_maintain_item(tmp_path):
 p=setup(tmp_path);eq=CraftedInstrumentEquipmentService(p)
 eq.equip(10,1,"lead guitar");eq.wear_band(1,10)
 with pytest.raises(ValueError,match="not found"):eq.repair(99,1)
