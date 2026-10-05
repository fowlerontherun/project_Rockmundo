import json, sqlite3
import pytest
from services.crafted_instrument_effects_service import CraftedInstrumentEffectsService
from services.crafted_instrument_equipment_service import CraftedInstrumentEquipmentService
from services.luthiery_stats_service import build_profile

def test_malformed_effect_payload_fails_closed(tmp_path):
 p=str(tmp_path/"bad.db")
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,stat_modifiers_json TEXT,condition_percent INTEGER)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,'{bad json',100)")
 assert CraftedInstrumentEffectsService(p).item_effects(10,1,"performance")==0.0

def test_equipment_uses_authoritative_band_role(tmp_path):
 p=str(tmp_path/"role.db")
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,instrument_type TEXT,name TEXT,serial_number TEXT)")
  c.execute("CREATE TABLE band_members(band_id INTEGER,character_id INTEGER,role TEXT)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,'guitar','G','S')")
  c.execute("INSERT INTO band_members VALUES(1,10,'bass')")
 svc=CraftedInstrumentEquipmentService(p)
 with pytest.raises(ValueError,match="incompatible"):
  svc.equip(10,1,"guitar")

def test_trait_changes_final_gameplay_modifier():
 class R(dict):
  def keys(self): return super().keys()
 material=R(stat_affinities_json=json.dumps({"sustain":20}))
 profile=build_profile([("body",material,None)],90,{"woodworking":100,"fretwork":100,"instrument_electronics":100,"instrument_finishing":100})
 assert any(t["key"]=="exceptional_sustain" for t in profile["traits"])
 final=profile["characteristics"]
 assert profile["gameplay_modifiers"]["instrument_effectiveness"]==round(sum(final.values())/len(final)/1800,4)
