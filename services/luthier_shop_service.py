"""Phase 8 player Luthier shops for serialized crafted instruments."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from services.luthiery_catalogue_service import DB_PATH
from services.economy_service import EconomyService,EconomyError\nfrom services.luthiery_reputation_service import LuthieryReputationService
class LuthierShopService:
 def __init__(self,db_path:str|None=None):self.db_path=str(db_path or DB_PATH);self.economy=EconomyService(db_path=self.db_path);self.reputation=LuthieryReputationService(self.db_path)
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
 def withdraw(self,seller:int,listing_id:int)->None:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   cur=c.execute("UPDATE luthier_shop_listings SET status='withdrawn' WHERE id=? AND seller_character_id=? AND status='active'",(listing_id,seller))
   if cur.rowcount!=1:raise ValueError("Active listing not found")
 def mine(self,seller:int)->dict:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row
   shop=c.execute("SELECT * FROM luthier_shops WHERE owner_character_id=?",(seller,)).fetchone()
   listings=[dict(r) for r in c.execute("""SELECT l.*,i.name instrument_name,i.serial_number,i.quality_tier
    FROM luthier_shop_listings l JOIN crafted_items i ON i.id=l.crafted_item_id WHERE l.seller_character_id=? ORDER BY l.id DESC""",(seller,))]
   sold=[x for x in listings if x["status"]=="sold"]
   revenue=sum(int(x["price_cents"]) for x in sold)
   return {"shop":dict(shop) if shop else None,"listings":listings,"summary":{"sold_count":len(sold),"gross_revenue_cents":revenue,"active_count":sum(1 for x in listings if x["status"]=="active")}}
 def listing_detail(self,listing_id:int)->dict:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row
   row=c.execute("""SELECT l.id listing_id,l.shop_id,l.crafted_item_id,l.seller_character_id,l.price_cents,l.status,
    l.buyer_character_id,l.created_at,l.sold_at,s.name shop_name,s.city_id shop_city_id,
    i.creator_character_id,i.owner_character_id,i.name,i.serial_number,i.instrument_type,i.shape_key,
    i.finish_key,i.primary_colour,i.accent_colour,i.hardware_colour,i.surface_sheen,i.quality_score,
    i.quality_tier,i.condition_percent,i.traits_json,i.stat_modifiers_json,i.genre_affinities_json,
    i.skill_snapshot_json,i.workshop_snapshot_json,i.created_at instrument_created_at
    FROM luthier_shop_listings l JOIN luthier_shops s ON s.id=l.shop_id
    JOIN crafted_items i ON i.id=l.crafted_item_id WHERE l.id=? AND l.status='active' AND i.owner_character_id=l.seller_character_id""",(listing_id,)).fetchone()
   if not row:raise ValueError("Listing is not available")
   result=dict(row)
   result["maker_reputation"]=self.reputation.profile(int(row["creator_character_id"]))["reputation"]\n   result["history"]=self.reputation.item_history(int(row["crafted_item_id"]))\n   result["parts"]=[dict(x) for x in c.execute("""SELECT p.part_type,p.material_key,m.name material_name,p.component_key,co.name component_name,p.quality_contribution
    FROM crafted_item_parts p LEFT JOIN crafting_materials m ON m.key=p.material_key LEFT JOIN crafting_component_designs co ON co.key=p.component_key
    WHERE p.crafted_item_id=? ORDER BY p.id""",(row["crafted_item_id"],))]
   return result
 def browse(self,query:str|None=None,instrument_type:str|None=None,min_price:int|None=None,max_price:int|None=None)->list[dict]:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row
   sql="""SELECT l.*,s.name shop_name,s.city_id,i.name instrument_name,i.serial_number,i.instrument_type,i.quality_tier,i.quality_score,i.condition_percent,i.shape_key,i.primary_colour,i.accent_colour,i.finish_key,i.workshop_snapshot_json
    FROM luthier_shop_listings l JOIN luthier_shops s ON s.id=l.shop_id JOIN crafted_items i ON i.id=l.crafted_item_id
    WHERE l.status='active' AND s.active=1 AND i.owner_character_id=l.seller_character_id"""
   params=[]
   if query:
    sql+=" AND (LOWER(i.name) LIKE ? OR LOWER(s.name) LIKE ? OR LOWER(i.serial_number) LIKE ?)"
    term="%"+query.strip().lower()+"%";params.extend([term,term,term])
   if instrument_type in ("guitar","bass"):sql+=" AND i.instrument_type=?";params.append(instrument_type)
   if min_price is not None:sql+=" AND l.price_cents>=?";params.append(max(0,int(min_price)))
   if max_price is not None:sql+=" AND l.price_cents<=?";params.append(max(0,int(max_price)))
   sql+=" ORDER BY l.id DESC"
   return [dict(r) for r in c.execute(sql,params)]
 def purchase(self,buyer:int,listing_id:int)->dict:
  """Atomically transfer payment, serialized ownership, listing state and provenance."""
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row;c.execute("PRAGMA foreign_keys=ON");c.execute("BEGIN IMMEDIATE")
   l=c.execute("""SELECT l.*,i.owner_character_id FROM luthier_shop_listings l JOIN crafted_items i ON i.id=l.crafted_item_id WHERE l.id=?""",(listing_id,)).fetchone()
   if not l or l["status"]!="active":raise ValueError("Listing is not available")
   seller=int(l["seller_character_id"]);price=int(l["price_cents"])
   if buyer==seller:raise ValueError("You cannot buy your own instrument")
   if int(l["owner_character_id"])!=seller:raise ValueError("Instrument ownership changed; listing is invalid")
   buyer_acct=c.execute("SELECT id,balance_cents FROM accounts WHERE user_id=? AND currency='USD'",(buyer,)).fetchone()
   if not buyer_acct or int(buyer_acct["balance_cents"])<price:raise ValueError("Insufficient funds")
   seller_acct=c.execute("SELECT id,balance_cents FROM accounts WHERE user_id=? AND currency='USD'",(seller,)).fetchone()
   if not seller_acct:
    c.execute("INSERT INTO accounts(user_id,currency,balance_cents) VALUES (?,'USD',0)",(seller,))
    seller_acct=c.execute("SELECT id,balance_cents FROM accounts WHERE user_id=? AND currency='USD'",(seller,)).fetchone()
   buyer_balance=int(buyer_acct["balance_cents"])-price;seller_balance=int(seller_acct["balance_cents"])+price
   c.execute("UPDATE accounts SET balance_cents=? WHERE id=?",(buyer_balance,buyer_acct["id"]))
   c.execute("UPDATE accounts SET balance_cents=? WHERE id=?",(seller_balance,seller_acct["id"]))
   tx=c.execute("""INSERT INTO transactions(type,amount_cents,currency,src_account_id,dest_account_id)
    VALUES ('luthiery_instrument_sale',?,'USD',?,?)""",(price,buyer_acct["id"],seller_acct["id"]))
   c.execute("INSERT INTO ledger_entries(account_id,transaction_id,delta_cents,balance_after) VALUES (?,?,?,?)",(buyer_acct["id"],tx.lastrowid,-price,buyer_balance))
   c.execute("INSERT INTO ledger_entries(account_id,transaction_id,delta_cents,balance_after) VALUES (?,?,?,?)",(seller_acct["id"],tx.lastrowid,price,seller_balance))
   changed=c.execute("UPDATE crafted_items SET owner_character_id=? WHERE id=? AND owner_character_id=?",(buyer,l["crafted_item_id"],seller))
   if changed.rowcount!=1:raise ValueError("Instrument ownership changed during purchase")
   sold=c.execute("UPDATE luthier_shop_listings SET status='sold',buyer_character_id=?,sold_at=datetime('now') WHERE id=? AND status='active'",(buyer,listing_id))
   if sold.rowcount!=1:raise ValueError("Listing changed during purchase")
   c.execute("INSERT INTO crafted_item_events(crafted_item_id,character_id,event_type,details_json) VALUES(?,?,'sold',?)",(l["crafted_item_id"],buyer,'{"seller_character_id":%d,"price_cents":%d}'%(seller,price)))
   return {"listing_id":listing_id,"crafted_item_id":l["crafted_item_id"],"price_cents":price,"seller_character_id":seller,"buyer_character_id":buyer,"maker_reputation_awarded":reputation_points}

luthier_shop_service=LuthierShopService()
