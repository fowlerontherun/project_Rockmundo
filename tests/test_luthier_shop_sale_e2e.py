import json,sqlite3,threading
from services.luthier_shop_service import LuthierShopService
from services.economy_service import EconomyService

def setup(tmp_path):
 p=str(tmp_path/"sale.db");s=LuthierShopService(p);s.ensure_schema()
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE IF NOT EXISTS crafted_items(id INTEGER PRIMARY KEY,creator_character_id INTEGER,owner_character_id INTEGER,locked INTEGER,instrument_type TEXT,name TEXT,serial_number TEXT,quality_tier TEXT,quality_score REAL,condition_percent INTEGER,shape_key TEXT,primary_colour TEXT,accent_colour TEXT,finish_key TEXT,workshop_snapshot_json TEXT,traits_json TEXT,stat_modifiers_json TEXT)")
  c.execute("CREATE TABLE IF NOT EXISTS character_equipped_crafted_instruments(character_id INTEGER PRIMARY KEY,crafted_item_id INTEGER)")
  c.execute("CREATE TABLE IF NOT EXISTS crafted_item_events(id INTEGER PRIMARY KEY,crafted_item_id INTEGER,character_id INTEGER,event_type TEXT,details_json TEXT,created_at TEXT DEFAULT(datetime('now')))")
  c.execute("CREATE TABLE IF NOT EXISTS crafted_item_parts(id INTEGER PRIMARY KEY,crafted_item_id INTEGER,part_type TEXT,material_key TEXT,component_key TEXT,quality_contribution REAL)")
  c.execute("CREATE TABLE IF NOT EXISTS crafting_materials(key TEXT PRIMARY KEY,name TEXT)")
  c.execute("CREATE TABLE IF NOT EXISTS crafting_component_designs(key TEXT PRIMARY KEY,name TEXT)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,10,0,'guitar','One','RM-1','Excellent',80,100,'shape','#111','#eee','solid','{}','[]','{}')")
 s.save_shop(10,"Shop");eco=EconomyService(p);eco.deposit(20,100000);return s,p,eco

def test_end_to_end_sale_moves_exact_serial_and_records_provenance(tmp_path):
 s,p,eco=setup(tmp_path);l=s.list_item(10,1,25000);result=s.purchase(20,l["id"])
 assert result["crafted_item_id"]==1
 with sqlite3.connect(p) as c:
  assert c.execute("SELECT owner_character_id,serial_number FROM crafted_items WHERE id=1").fetchone()==(20,"RM-1")
  assert c.execute("SELECT status,buyer_character_id FROM luthier_shop_listings WHERE id=?",(l["id"],)).fetchone()==("sold",20)
  assert c.execute("SELECT event_type FROM crafted_item_events WHERE crafted_item_id=1").fetchone()[0]=="sold"
 assert eco.get_balance(20)==75000 and eco.get_balance(10)==25000

def test_duplicate_purchase_is_rejected_without_second_charge(tmp_path):
 s,p,eco=setup(tmp_path);l=s.list_item(10,1,25000);s.purchase(20,l["id"]);before=eco.get_balance(20)
 try:s.purchase(20,l["id"])
 except ValueError:pass
 else:raise AssertionError("duplicate purchase should fail")
 assert eco.get_balance(20)==before
