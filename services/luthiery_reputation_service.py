"""Phase 9 Luthier reputation and collectible provenance."""
from __future__ import annotations
import json,sqlite3
from services.luthiery_catalogue_service import DB_PATH

class LuthieryReputationService:
 def __init__(self,db_path=None):self.db_path=str(db_path or DB_PATH)
 def ensure_schema(self):
  with sqlite3.connect(self.db_path) as c:
   c.executescript("""CREATE TABLE IF NOT EXISTS luthier_reputation_events(
    id INTEGER PRIMARY KEY AUTOINCREMENT,luthier_character_id INTEGER NOT NULL,crafted_item_id INTEGER,
    event_type TEXT NOT NULL,points INTEGER NOT NULL,source_character_id INTEGER,details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT(datetime('now')));
    CREATE INDEX IF NOT EXISTS ix_luthier_rep_owner ON luthier_reputation_events(luthier_character_id,created_at);
    CREATE TABLE IF NOT EXISTS crafted_item_notable_history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,crafted_item_id INTEGER NOT NULL,event_type TEXT NOT NULL,
    character_id INTEGER,details_json TEXT NOT NULL DEFAULT '{}',created_at TEXT NOT NULL DEFAULT(datetime('now')));
    CREATE INDEX IF NOT EXISTS ix_luthier_notable_item ON crafted_item_notable_history(crafted_item_id,created_at);""")
 def award_sale(self,conn,item_id:int,buyer:int,price:int)->int:
  row=conn.execute("SELECT creator_character_id,quality_score FROM crafted_items WHERE id=?",(item_id,)).fetchone()
  if not row:return 0
  creator=int(row[0]);quality=float(row[1] or 0)
  prior=conn.execute("SELECT COUNT(*) FROM luthier_reputation_events WHERE luthier_character_id=? AND event_type='sale' AND source_character_id=?",(creator,buyer)).fetchone()[0]
  base=2+(2 if quality>=84 else 1 if quality>=72 else 0)
  points=max(1,base//(1+int(prior)//3))
  conn.execute("INSERT INTO luthier_reputation_events(luthier_character_id,crafted_item_id,event_type,points,source_character_id,details_json) VALUES(?,?,'sale',?,?,?)",(creator,item_id,points,buyer,json.dumps({"price_cents":price,"quality_score":quality})))
  conn.execute("INSERT INTO crafted_item_notable_history(crafted_item_id,event_type,character_id,details_json) VALUES(?,'owner',?,?)",(item_id,buyer,json.dumps({"acquired_price_cents":price})))
  return points
 def profile(self,character_id:int)->dict:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row
   row=c.execute("SELECT COALESCE(SUM(points),0) reputation,COUNT(*) events FROM luthier_reputation_events WHERE luthier_character_id=?",(character_id,)).fetchone()
   return {"reputation":int(row["reputation"]),"events":int(row["events"])}
 def item_history(self,item_id:int)->list[dict]:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row
   return [dict(r) for r in c.execute("SELECT * FROM crafted_item_notable_history WHERE crafted_item_id=? ORDER BY id DESC",(item_id,))]
luthiery_reputation=LuthieryReputationService()
