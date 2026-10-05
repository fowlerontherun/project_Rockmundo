import sqlite3,pytest
from services.luthier_shop_service import LuthierShopService
def setup(tmp_path):
 p=str(tmp_path/"shops.db");s=LuthierShopService(p);s.ensure_schema()
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE IF NOT EXISTS crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,locked INTEGER,instrument_type TEXT,name TEXT,serial_number TEXT,quality_tier TEXT,quality_score REAL,condition_percent INTEGER,shape_key TEXT,primary_colour TEXT,accent_colour TEXT,finish_key TEXT,workshop_snapshot_json TEXT)")
  c.execute("CREATE TABLE IF NOT EXISTS character_equipped_crafted_instruments(character_id INTEGER PRIMARY KEY,crafted_item_id INTEGER)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,0,'guitar','One','RM-1','Good',65,100,'shape','#111111','#eeeeee','luthier.finish.solid','{}')")
 s.save_shop(10,"Shop");return s
def test_only_seller_can_withdraw_and_history_retains_withdrawn(tmp_path):
 s=setup(tmp_path);l=s.list_item(10,1,10000)
 with pytest.raises(ValueError):s.withdraw(20,l["id"])
 s.withdraw(10,l["id"])
 mine=s.mine(10);assert mine["listings"][0]["status"]=="withdrawn"
 assert s.browse()==[]
