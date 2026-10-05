import json,sqlite3,pytest
from services.crafted_instrument_equipment_service import CraftedInstrumentEquipmentService
from services.crafted_instrument_effects_service import CraftedInstrumentEffectsService

def setup(tmp_path):
 p=str(tmp_path/"switch.db")
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,instrument_type TEXT,name TEXT,serial_number TEXT,stat_modifiers_json TEXT,condition_percent INTEGER)")
  c.execute("CREATE TABLE band_members(band_id INTEGER,character_id INTEGER,role TEXT)")
  c.executemany("INSERT INTO crafted_items VALUES(?,?,?,?,?,?,?,?)",[
   (1,10,'guitar','One','S1',json.dumps({"performance_quality":.04}),100),
   (2,20,'bass','Two','S2',json.dumps({"performance_quality":.07}),100)])
  c.executemany("INSERT INTO band_members VALUES(1,?,?)",[(10,'lead guitar'),(20,'bass')])
 return p

def test_character_switch_keeps_equipment_isolated(tmp_path):
 p=setup(tmp_path);eq=CraftedInstrumentEquipmentService(p);fx=CraftedInstrumentEffectsService(p)
 eq.equip(10,1,'lead guitar');eq.equip(20,2,'bass')
 assert eq.equipped(10)['id']==1 and eq.equipped(20)['id']==2
 with pytest.raises(ValueError):eq.equip(10,2,'lead guitar')
 eq.unequip(10)
 assert eq.equipped(10) is None and eq.equipped(20)['id']==2
 assert fx.band_effects(1,'performance')==.07
