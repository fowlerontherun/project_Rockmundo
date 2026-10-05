import json,sqlite3,pytest
from services.luthiery_crafting_service import LuthieryCraftingService
from services.luthier_shop_service import LuthierShopService
from services.economy_service import EconomyService

def stocked_service(tmp_path):
 p=str(tmp_path/"craft.db");s=LuthieryCraftingService(p);s.ensure_schema()
 with sqlite3.connect(p) as c:
  ids={r[1]:r[0] for r in c.execute("SELECT id,key FROM crafting_materials")}
  for key in ("luthier.material.basswood","luthier.material.maple","luthier.material.rosewood"):
   c.execute("INSERT INTO character_crafting_materials(character_id,material_id,quantity) VALUES(1,?,10)",(ids[key],))
 return s,p

def test_rejects_invalid_hex_and_wrong_part_material(tmp_path):
 s,p=stocked_service(tmp_path)
 sel={x:{"material_key":"luthier.material.maple"} for x in ("body","neck","fretboard","electronics","hardware")}
 with pytest.raises(ValueError,match="primary colour"):s.craft(1,"a","x","guitar","luthier.shape.guitar.double_cut",sel,{"luthiery":100,"instrument_finishing":100},primary_colour="#GGGGGG")
 sel["body"]={"material_key":"luthier.material.rosewood"}
 with pytest.raises(ValueError,match="cannot be used for body"):s.craft(1,"b","x","guitar","luthier.shape.guitar.double_cut",sel,{"luthiery":100,"instrument_finishing":100})

def test_failed_serial_transfer_rolls_back_money(tmp_path):
 p=str(tmp_path/"sale.db");s=LuthierShopService(p);s.ensure_schema()
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE IF NOT EXISTS crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,locked INTEGER,instrument_type TEXT,name TEXT,serial_number TEXT,quality_tier TEXT,quality_score REAL,condition_percent INTEGER)")
  c.execute("CREATE TABLE IF NOT EXISTS character_equipped_crafted_instruments(character_id INTEGER PRIMARY KEY,crafted_item_id INTEGER)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,0,'guitar','G','S','Good',60,100)")
 s.save_shop(10,"Shop");listing=s.list_item(10,1,5000);eco=EconomyService(p);eco.deposit(20,10000)
 with sqlite3.connect(p) as c:c.execute("UPDATE crafted_items SET owner_character_id=99 WHERE id=1")
 before=eco.get_balance(20)
 with pytest.raises(ValueError,match="ownership changed"):s.purchase(20,listing["id"])
 assert eco.get_balance(20)==before
