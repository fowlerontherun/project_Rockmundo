import sqlite3,pytest
from services.luthier_shop_service import LuthierShopService

def setup(tmp_path):
 p=str(tmp_path/"shop.db");s=LuthierShopService(p);s.ensure_schema()
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE IF NOT EXISTS crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,locked INTEGER,instrument_type TEXT,name TEXT,serial_number TEXT,quality_tier TEXT,quality_score REAL,condition_percent INTEGER)")
  c.execute("CREATE TABLE IF NOT EXISTS character_equipped_crafted_instruments(character_id INTEGER PRIMARY KEY,crafted_item_id INTEGER)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,0,'guitar','Handbuilt','RM-1','Excellent',75,100)")
 s.save_shop(10,"Ten Guitars")
 return s,p

def test_listing_is_serialized_owner_safe_and_locked_items_blocked(tmp_path):
 s,p=setup(tmp_path);listing=s.list_item(10,1,50000)
 assert listing["crafted_item_id"]==1
 with pytest.raises(ValueError):s.list_item(99,1,50000)
 with sqlite3.connect(p) as c:c.execute("UPDATE crafted_items SET locked=1 WHERE id=1");c.execute("UPDATE luthier_shop_listings SET status='withdrawn'")
 with pytest.raises(ValueError,match="Unlock"):s.list_item(10,1,50000)

def test_browse_exposes_exact_instrument(tmp_path):
 s,p=setup(tmp_path);s.list_item(10,1,50000);row=s.browse()[0]
 assert row["serial_number"]=="RM-1" and row["instrument_name"]=="Handbuilt" and row["price_cents"]==50000
