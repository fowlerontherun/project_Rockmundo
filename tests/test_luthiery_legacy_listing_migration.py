import sqlite3
from pathlib import Path

def test_legacy_listing_constraint_is_detectable_and_history_preserved(tmp_path):
 p=tmp_path/"legacy.db"
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE luthier_shops(id INTEGER PRIMARY KEY,owner_character_id INTEGER UNIQUE,name TEXT,description TEXT,city_id INTEGER,active INTEGER,created_at TEXT)")
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY)")
  c.execute("""CREATE TABLE luthier_shop_listings(id INTEGER PRIMARY KEY,shop_id INTEGER,crafted_item_id INTEGER,seller_character_id INTEGER,price_cents INTEGER,status TEXT,buyer_character_id INTEGER,created_at TEXT,sold_at TEXT,UNIQUE(crafted_item_id,status))""")
  c.execute("INSERT INTO luthier_shops VALUES(1,10,'Shop','',NULL,1,'now')")
  c.execute("INSERT INTO crafted_items VALUES(1)")
  c.execute("INSERT INTO luthier_shop_listings VALUES(1,1,1,10,1000,'withdrawn',NULL,'now',NULL)")
 ddl=sqlite3.connect(p).execute("SELECT sql FROM sqlite_master WHERE name='luthier_shop_listings'").fetchone()[0]
 assert "UNIQUE(crafted_item_id,status)" in ddl.replace(" ","")
