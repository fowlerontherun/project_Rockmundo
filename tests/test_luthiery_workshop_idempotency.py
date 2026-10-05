import sqlite3
from services.luthiery_workshop_service import LuthieryWorkshopService

def test_duplicate_upgrade_token_debits_once(tmp_path):
 p=tmp_path/"w.db"
 with sqlite3.connect(p) as c:
  c.executescript("""CREATE TABLE accounts(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,currency TEXT,balance_cents INTEGER);
  CREATE TABLE transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,type TEXT,amount_cents INTEGER,currency TEXT,src_account_id INTEGER,dest_account_id INTEGER);
  CREATE TABLE ledger_entries(id INTEGER PRIMARY KEY AUTOINCREMENT,account_id INTEGER,transaction_id INTEGER,delta_cents INTEGER,balance_after INTEGER);""")
  c.execute("INSERT INTO accounts(user_id,currency,balance_cents) VALUES(10,'USD',200000)")
 svc=LuthieryWorkshopService(p)
 a=svc.upgrade(10,"same-token");b=svc.upgrade(10,"same-token")
 assert a["upgrade_level"]==1 and b["upgrade_level"]==1
 with sqlite3.connect(p) as c:
  assert c.execute("SELECT balance_cents FROM accounts WHERE user_id=10").fetchone()[0]==175000
  assert c.execute("SELECT COUNT(*) FROM transactions WHERE type='luthiery_workshop_upgrade'").fetchone()[0]==1
  assert c.execute("SELECT COUNT(*) FROM luthiery_workshop_upgrade_requests").fetchone()[0]==1
