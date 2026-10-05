import sqlite3
from services.luthier_shop_service import LuthierShopService

def test_listing_detail_keeps_listing_and_crafted_item_ids_distinct(tmp_path):
 p=str(tmp_path/"shop.db");svc=LuthierShopService(p);svc.ensure_schema()
 with sqlite3.connect(p) as c:
  c.execute("""CREATE TABLE IF NOT EXISTS crafted_items(id INTEGER PRIMARY KEY,creator_character_id INTEGER,owner_character_id INTEGER,name TEXT,serial_number TEXT,instrument_type TEXT,shape_key TEXT,finish_key TEXT,primary_colour TEXT,accent_colour TEXT,hardware_colour TEXT,surface_sheen TEXT,quality_score REAL,quality_tier TEXT,condition_percent INTEGER,traits_json TEXT,stat_modifiers_json TEXT,genre_affinities_json TEXT,skill_snapshot_json TEXT,workshop_snapshot_json TEXT,created_at TEXT,locked INTEGER DEFAULT 0)""")
  c.execute("INSERT INTO crafted_items VALUES(42,10,10,'Axe','RM-42','guitar','shape','finish','#000','#111','#222','gloss',80,'Excellent',100,'[]','{}','{}','{}','{}','now',0)")
 shop=svc.save_shop(10,"Maker");listing=svc.list_item(10,42,12345)
 detail=svc.listing_detail(listing["id"])
 assert detail["listing_id"]==listing["id"]
 assert detail["crafted_item_id"]==42
 assert detail["serial_number"]=="RM-42"
