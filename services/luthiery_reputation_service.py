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
    CREATE INDEX IF NOT EXISTS ix_luthier_notable_item ON crafted_item_notable_history(crafted_item_id,created_at);\n    CREATE UNIQUE INDEX IF NOT EXISTS ux_luthier_notable_event ON crafted_item_notable_history(crafted_item_id,event_type,details_json);""")
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
 def record_notable_use(self,item_id:int,event_type:str,event_id:int,character_id:int|None=None,fame:int=0,details:dict|None=None)->int:
  if event_type not in ("notable_gig","notable_recording"):raise ValueError("Unsupported notable event")
  self.ensure_schema();details={**(details or {}),"event_id":int(event_id),"fame":int(fame)}
  with sqlite3.connect(self.db_path) as c:
   row=c.execute("SELECT creator_character_id,quality_score FROM crafted_items WHERE id=?",(item_id,)).fetchone()
   if not row:return 0
   payload=json.dumps(details,sort_keys=True,separators=(",",":"))
   try:c.execute("INSERT INTO crafted_item_notable_history(crafted_item_id,event_type,character_id,details_json) VALUES(?,?,?,?)",(item_id,event_type,character_id,payload))
   except sqlite3.IntegrityError:return 0
   points=3+(2 if fame>=1000 else 1 if fame>=250 else 0)+(1 if float(row[1] or 0)>=84 else 0)
   c.execute("INSERT INTO luthier_reputation_events(luthier_character_id,crafted_item_id,event_type,points,source_character_id,details_json) VALUES(?,?,?,?,?,?)",(int(row[0]),item_id,event_type,points,character_id,payload))
   return points
 def desirability(self,item_id:int)->dict:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   row=c.execute("SELECT creator_character_id,quality_score FROM crafted_items WHERE id=?",(item_id,)).fetchone()
   if not row:return {"score":0,"tier":"ordinary"}
   rep=c.execute("SELECT COALESCE(SUM(points),0) FROM luthier_reputation_events WHERE luthier_character_id=?",(int(row[0]),)).fetchone()[0]
   owners=c.execute("SELECT COUNT(*) FROM crafted_item_notable_history WHERE crafted_item_id=? AND event_type='owner'",(item_id,)).fetchone()[0]
   notable=c.execute("SELECT COUNT(*) FROM crafted_item_notable_history WHERE crafted_item_id=? AND event_type IN ('notable_gig','notable_recording')",(item_id,)).fetchone()[0]
   score=min(100,round(float(row[1] or 0)*.55+min(20,int(rep)*.2)+min(10,int(owners)*2)+min(15,int(notable)*5)))
   tier="iconic" if score>=90 else "collectible" if score>=75 else "notable" if score>=60 else "ordinary"
   return {"score":score,"tier":tier}
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
