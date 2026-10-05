import sqlite3
import pytest
from services.luthiery_workshop_service import LuthieryWorkshopService

def _db(tmp_path,balance=100000):
 p=tmp_path/"workshop.db"
 with sqlite3.connect(p) as c:
  c.executescript("""CREATE TABLE accounts(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,currency TEXT,balance_cents INTEGER);
  CREATE TABLE transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,type TEXT,amount_cents INTEGER,currency TEXT,src_account_id INTEGER,dest_account_id INTEGER);
  CREATE TABLE ledger_entries(id INTEGER PRIMARY KEY AUTOINCREMENT,account_id INTEGER,transaction_id INTEGER,delta_cents INTEGER,balance_after INTEGER);""")
  c.execute("INSERT INTO accounts(user_id,currency,balance_cents) VALUES(10,'EUR',999999)")
  c.execute("INSERT INTO accounts(user_id,currency,balance_cents) VALUES(10,'USD',?)",(balance,))
 return p

def test_upgrade_debits_usd_once_and_advances_quality(tmp_path):
 p=_db(tmp_path);svc=LuthieryWorkshopService(p)
 out=svc.upgrade(10)
 assert out["upgrade_level"]==1 and out["quality_score"]==60
 with sqlite3.connect(p) as c:
  assert c.execute("SELECT balance_cents FROM accounts WHERE user_id=10 AND currency='USD'").fetchone()[0]==75000
  assert c.execute("SELECT balance_cents FROM accounts WHERE user_id=10 AND currency='EUR'").fetchone()[0]==999999
  assert c.execute("SELECT COUNT(*) FROM transactions WHERE type='luthiery_workshop_upgrade'").fetchone()[0]==1
  assert c.execute("SELECT delta_cents,balance_after FROM ledger_entries").fetchone()==(-25000,75000)

def test_upgrade_is_atomic_on_insufficient_funds(tmp_path):
 p=_db(tmp_path,24999);svc=LuthieryWorkshopService(p)
 with pytest.raises(ValueError,match="Insufficient funds"):svc.upgrade(10)
 assert svc.get(10)["upgrade_level"]==0
 with sqlite3.connect(p) as c:
  assert c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]==0

def test_max_workshop_cannot_upgrade(tmp_path):
 p=_db(tmp_path,2000000);svc=LuthieryWorkshopService(p);svc.ensure_schema()
 with sqlite3.connect(p) as c:c.execute("INSERT INTO character_luthiery_workshops(character_id,quality_score,upgrade_level) VALUES(10,100,5)")
 with pytest.raises(ValueError,match="fully upgraded"):svc.upgrade(10)
