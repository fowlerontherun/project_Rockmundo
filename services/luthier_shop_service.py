"""Phase 8 player Luthier shops for serialized crafted instruments."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from services.luthiery_catalogue_service import DB_PATH
from services.economy_service import EconomyService,EconomyError
class LuthierShopService:
 def __init__(self,db_path:str|None=None):self.db_path=str(db_path or DB_PATH);self.economy=EconomyService(db_path=self.db_path)
 def ensure_schema(self):
  self.economy.ensure_schema();sql=Path(__file__).resolve().parents[1]/"migrations/sql/174_luthiery_phase8_shops.sql"
  with sqlite3.connect(self.db_path) as c:c.executescript(sql.read_text())
 def save_shop(self,owner:int,name:str,description:str="",city_id:int|None=None)->dict:
  self.ensure_schema();name=name.strip()[:80]
  if not name:raise ValueError("Shop name is required")
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row
   c.execute("""INSERT INTO luthier_shops(owner_character_id,name,description,city_id) VALUES(?,?,?,?)
    ON CONFLICT(owner_character_id) DO UPDATE SET name=excluded.name,description=excluded.description,city_id=excluded.city_id,active=1""",(owner,name,description.strip()[:500],city_id))
   return dict(c.execute("SELECT * FROM luthier_shops WHERE owner_character_id=?",(owner,)).fetchone())
 def list_item(self,seller:int,item_id:int,price:int)->dict:
  self.ensure_schema()
  if price<=0:raise ValueError("Price must be positive")
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row;c.execute("BEGIN IMMEDIATE")
   shop=c.execute("SELECT * FROM luthier_shops WHERE owner_character_id=? AND active=1",(seller,)).fetchone()
   if not shop:raise ValueError("Open a Luthier shop before listing instruments")
   item=c.execute("SELECT id,locked FROM crafted_items WHERE id=? AND owner_character_id=?",(item_id,seller)).fetchone()
   if not item:raise ValueError("Crafted instrument not found")
   if item["locked"]:raise ValueError("Unlock the instrument before listing it")
   equipped=c.execute("SELECT 1 FROM character_equipped_crafted_instruments WHERE character_id=? AND crafted_item_id=?",(seller,item_id)).fetchone()
   if equipped:raise ValueError("Unequip the instrument before listing it")
   existing=c.execute("SELECT 1 FROM luthier_shop_listings WHERE crafted_item_id=? AND status='active'",(item_id,)).fetchone()
   if existing:raise ValueError("Instrument is already listed")
   cur=c.execute("INSERT INTO luthier_shop_listings(shop_id,crafted_item_id,seller_character_id,price_cents) VALUES(?,?,?,?)",(shop["id"],item_id,seller,price))
   return dict(c.execute("SELECT * FROM luthier_shop_listings WHERE id=?",(cur.lastrowid,)).fetchone())
 def browse(self)->list[dict]:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row
   return [dict(r) for r in c.execute("""SELECT l.*,s.name shop_name,i.name instrument_name,i.serial_number,i.instrument_type,i.quality_tier,i.quality_score,i.condition_percent
    FROM luthier_shop_listings l JOIN luthier_shops s ON s.id=l.shop_id JOIN crafted_items i ON i.id=l.crafted_item_id
    WHERE l.status='active' AND s.active=1 AND i.owner_character_id=l.seller_character_id ORDER BY l.id DESC""")]
 def purchase(self,buyer:int,listing_id:int)->dict:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row;c.execute("BEGIN IMMEDIATE")
   l=c.execute("""SELECT l.*,i.owner_character_id FROM luthier_shop_listings l JOIN crafted_items i ON i.id=l.crafted_item_id WHERE l.id=?""",(listing_id,)).fetchone()
   if not l or l["status"]!="active":raise ValueError("Listing is not available")
   seller=int(l["seller_character_id"])
   if buyer==seller:raise ValueError("You cannot buy your own instrument")
   if int(l["owner_character_id"])!=seller:raise ValueError("Instrument ownership changed; listing is invalid")
   try:self.economy.transfer(buyer,seller,int(l["price_cents"]))
   except EconomyError as exc:raise ValueError(str(exc)) from exc
   # Recheck ownership immediately before the serialized transfer.
   changed=c.execute("UPDATE crafted_items SET owner_character_id=? WHERE id=? AND owner_character_id=?",(buyer,l["crafted_item_id"],seller))
   if changed.rowcount!=1:raise ValueError("Instrument ownership changed during purchase")
   c.execute("UPDATE luthier_shop_listings SET status='sold',buyer_character_id=?,sold_at=datetime('now') WHERE id=? AND status='active'",(buyer,listing_id))
   try:c.execute("INSERT INTO crafted_item_events(crafted_item_id,character_id,event_type,details_json) VALUES(?,?,'sold',?)",(l["crafted_item_id"],buyer,'{"seller_character_id":%d,"price_cents":%d}'%(seller,l["price_cents"])))
   except sqlite3.OperationalError:pass
   return {"listing_id":listing_id,"crafted_item_id":l["crafted_item_id"],"price_cents":l["price_cents"],"seller_character_id":seller,"buyer_character_id":buyer}
luthier_shop_service=LuthierShopService()
