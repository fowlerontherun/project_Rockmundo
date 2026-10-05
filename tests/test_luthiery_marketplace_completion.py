import sqlite3
from services.luthier_shop_service import LuthierShopService
from services.economy_service import EconomyService

def setup(tmp_path):
 p=str(tmp_path/"market.db");s=LuthierShopService(p);s.ensure_schema()
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE IF NOT EXISTS crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,locked INTEGER,instrument_type TEXT,name TEXT,serial_number TEXT,quality_tier TEXT,quality_score REAL,condition_percent INTEGER,shape_key TEXT,primary_colour TEXT,accent_colour TEXT,finish_key TEXT,workshop_snapshot_json TEXT)")
  c.execute("CREATE TABLE IF NOT EXISTS character_equipped_crafted_instruments(character_id INTEGER PRIMARY KEY,crafted_item_id INTEGER)")
  c.execute("CREATE TABLE IF NOT EXISTS crafted_item_events(id INTEGER PRIMARY KEY AUTOINCREMENT,crafted_item_id INTEGER,character_id INTEGER,event_type TEXT,details_json TEXT)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,0,'guitar','Nightbird','RM-G-1','Excellent',80,100,'shape','#111','#eee','finish','{}')")
  c.execute("INSERT INTO crafted_items VALUES(2,10,0,'bass','Thunder Bass','RM-B-2','Good',70,100,'shape','#111','#eee','finish','{}')")
 s.save_shop(10,"Blackbird Instruments");s.list_item(10,1,25000);s.list_item(10,2,18000)
 return s,p

def test_marketplace_filters(tmp_path):
 s,p=setup(tmp_path)
 assert [x["instrument_name"] for x in s.browse(query="night")]==["Nightbird"]
 assert [x["instrument_name"] for x in s.browse(instrument_type="bass")]==["Thunder Bass"]
 assert [x["instrument_name"] for x in s.browse(min_price=20000)]==["Nightbird"]

def test_sales_summary(tmp_path):
 s,p=setup(tmp_path);eco=EconomyService(p);eco.deposit(20,50000);listing=s.browse(query="night")[0]
 s.purchase(20,listing["id"]);mine=s.mine(10)
 assert mine["summary"]["sold_count"]==1
 assert mine["summary"]["gross_revenue_cents"]==25000
 assert mine["summary"]["active_count"]==1
