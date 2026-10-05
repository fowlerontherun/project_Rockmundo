"""Persistent server-authoritative Luthiery workshop progression."""
import sqlite3
from pathlib import Path
from services.luthiery_catalogue_service import DB_PATH

BASE_QUALITY=50
UPGRADE_QUALITIES=(50,60,70,80,90,100)
UPGRADE_COSTS_CENTS=(0,25000,75000,200000,500000,1000000)

class LuthieryWorkshopService:
 def __init__(self,db_path=None):self.db_path=str(db_path or DB_PATH)
 def ensure_schema(self):
  sql=Path(__file__).resolve().parents[1]/"migrations/sql/177_luthiery_workshop_quality.sql"
  with sqlite3.connect(self.db_path) as c:c.executescript(sql.read_text())
 def get(self,character_id:int)->dict:
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row
   row=c.execute("SELECT * FROM character_luthiery_workshops WHERE character_id=?",(character_id,)).fetchone()
   if not row:out={"character_id":character_id,"quality_score":BASE_QUALITY,"upgrade_level":0}
   else:out=dict(row)
   level=int(out["upgrade_level"]);out["next_upgrade_cost_cents"]=UPGRADE_COSTS_CENTS[level+1] if level<5 else None
   account=c.execute("SELECT balance_cents FROM accounts WHERE user_id=? AND currency='USD'",(character_id,)).fetchone()
   out["balance_cents"]=int(account[0]) if account else 0
   out["can_afford_next_upgrade"]=out["next_upgrade_cost_cents"] is not None and out["balance_cents"]>=out["next_upgrade_cost_cents"]
   return out
 def quality(self,character_id:int)->float:return float(self.get(character_id)["quality_score"])
 def upgrade(self,character_id:int,request_token:str)->dict:
  if not request_token or not request_token.strip():raise ValueError("An upgrade request token is required")
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   c.row_factory=sqlite3.Row;c.execute("BEGIN IMMEDIATE")
   prior=c.execute("SELECT resulting_level FROM luthiery_workshop_upgrade_requests WHERE character_id=? AND request_token=?",(character_id,request_token)).fetchone()
   if prior:return self.get(character_id)
   row=c.execute("SELECT quality_score,upgrade_level FROM character_luthiery_workshops WHERE character_id=?",(character_id,)).fetchone()
   level=int(row["upgrade_level"]) if row else 0
   if level>=5:raise ValueError("Luthiery workshop is already fully upgraded")
   next_level=level+1;cost=UPGRADE_COSTS_CENTS[next_level]
   account=c.execute("SELECT id,balance_cents FROM accounts WHERE user_id=? AND currency='USD'",(character_id,)).fetchone()
   if not account or int(account["balance_cents"])<cost:raise ValueError("Insufficient funds for workshop upgrade")
   new_balance=int(account["balance_cents"])-cost
   c.execute("UPDATE accounts SET balance_cents=? WHERE id=?",(new_balance,account["id"]))
   tx=c.execute("INSERT INTO transactions(type,amount_cents,currency,src_account_id) VALUES('luthiery_workshop_upgrade',?,'USD',?)",(cost,account["id"]))
   c.execute("INSERT INTO ledger_entries(account_id,transaction_id,delta_cents,balance_after) VALUES(?,?,?,?)",(account["id"],tx.lastrowid,-cost,new_balance))
   c.execute("""INSERT INTO character_luthiery_workshops(character_id,quality_score,upgrade_level,updated_at) VALUES(?,?,?,datetime('now'))
    ON CONFLICT(character_id) DO UPDATE SET quality_score=excluded.quality_score,upgrade_level=excluded.upgrade_level,updated_at=excluded.updated_at""",(character_id,UPGRADE_QUALITIES[next_level],next_level))
   c.execute("INSERT INTO luthiery_workshop_upgrade_requests(character_id,request_token,resulting_level,transaction_id) VALUES(?,?,?,?)",(character_id,request_token,next_level,tx.lastrowid))
  return self.get(character_id)

luthiery_workshop_service=LuthieryWorkshopService()
