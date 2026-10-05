"""Authoritative Phase 7 equip/unequip operations for crafted instruments."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from services.luthiery_catalogue_service import DB_PATH

ROLE_TYPES={"guitar":"guitar","lead guitar":"guitar","rhythm guitar":"guitar","bass":"bass","bass guitar":"bass"}

class CraftedInstrumentEquipmentService:
 def __init__(self,db_path:str|None=None): self.db_path=str(db_path or DB_PATH)
 def ensure_schema(self):
  sql=Path(__file__).resolve().parents[1]/"migrations/sql/173_luthiery_phase7_equipment.sql"
  with sqlite3.connect(self.db_path) as c: c.executescript(sql.read_text())
 def equip(self,character_id:int,item_id:int,role:str|None=None)->dict:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row;c.execute("BEGIN IMMEDIATE")
   item=c.execute("SELECT id,instrument_type,name,serial_number FROM crafted_items WHERE id=? AND owner_character_id=?",(item_id,character_id)).fetchone()
   if not item: raise ValueError("Crafted instrument not found or not owned by this character")
   if role:
    expected=ROLE_TYPES.get(role.strip().lower())
    if expected and expected!=item["instrument_type"]: raise ValueError("Instrument is incompatible with this band role")
   c.execute("""INSERT INTO character_equipped_crafted_instruments(character_id,crafted_item_id)
     VALUES (?,?) ON CONFLICT(character_id) DO UPDATE SET crafted_item_id=excluded.crafted_item_id,equipped_at=datetime('now')""",(character_id,item_id))
   return dict(item)
 def unequip(self,character_id:int)->None:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:c.execute("DELETE FROM character_equipped_crafted_instruments WHERE character_id=?",(character_id,))
 def equipped(self,character_id:int)->dict|None:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row
   r=c.execute("""SELECT i.* FROM character_equipped_crafted_instruments e JOIN crafted_items i ON i.id=e.crafted_item_id
     WHERE e.character_id=? AND i.owner_character_id=e.character_id""",(character_id,)).fetchone()
   return dict(r) if r else None
 def wear_band(self,band_id:int,amount:int)->int:
  if amount<=0:return 0
  equipment=self.band_equipment(band_id)
  if not equipment:return 0
  with sqlite3.connect(self.db_path) as c:
   changed=0
   for cid,iid in equipment.items():
    cur=c.execute("""UPDATE crafted_items SET condition_percent=MAX(0,condition_percent-?)
      WHERE id=? AND owner_character_id=?""",(amount,iid,cid))
    changed+=cur.rowcount
   return changed

 def repair(self,character_id:int,item_id:int,amount:int=25)->dict:
  self.ensure_schema()
  if amount<=0 or amount>100:raise ValueError("Repair amount must be between 1 and 100")
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row;c.execute("BEGIN IMMEDIATE")
   item=c.execute("SELECT * FROM crafted_items WHERE id=? AND owner_character_id=?",(item_id,character_id)).fetchone()
   if not item:raise ValueError("Crafted instrument not found")
   current=int(item["condition_percent"])
   if current>=100:raise ValueError("Instrument does not need maintenance")
   restored=min(amount,100-current)
   # Maintenance is intentionally modest and deterministic; economy charging can be layered by shop/workshop later.
   c.execute("UPDATE crafted_items SET condition_percent=condition_percent+? WHERE id=?",(restored,item_id))
   try:c.execute("""INSERT INTO crafted_item_events(crafted_item_id,character_id,event_type,details_json)
     VALUES (?,?,'maintained',?)""",(item_id,character_id,'{"condition_restored":%d}'%restored))
   except sqlite3.OperationalError:pass
   return dict(c.execute("SELECT * FROM crafted_items WHERE id=?",(item_id,)).fetchone())

 def band_equipment(self,band_id:int)->dict[int,int]:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   try:
    rows=c.execute("""SELECT bm.character_id,e.crafted_item_id FROM band_members bm
      JOIN character_equipped_crafted_instruments e ON e.character_id=bm.character_id
      JOIN crafted_items i ON i.id=e.crafted_item_id AND i.owner_character_id=bm.character_id
      WHERE bm.band_id=?""",(band_id,)).fetchall()
   except sqlite3.OperationalError:return {}
   return {int(cid):int(iid) for cid,iid in rows}
crafted_instrument_equipment=CraftedInstrumentEquipmentService()
