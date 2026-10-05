import sqlite3,pytest
from services.crafted_instrument_equipment_service import CraftedInstrumentEquipmentService

def setup(tmp_path):
 p=str(tmp_path/"wear.db");s=CraftedInstrumentEquipmentService(p);s.ensure_schema()
 with sqlite3.connect(p) as c:
  c.executescript("""CREATE TABLE IF NOT EXISTS crafted_items(id INTEGER PRIMARY KEY,owner_character_id INTEGER,instrument_type TEXT,name TEXT,serial_number TEXT,condition_percent INTEGER);
  CREATE TABLE IF NOT EXISTS band_members(band_id INTEGER,character_id INTEGER,role TEXT);
  CREATE TABLE IF NOT EXISTS accounts(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,currency TEXT,balance_cents INTEGER);
  CREATE TABLE IF NOT EXISTS transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,type TEXT,amount_cents INTEGER,currency TEXT,src_account_id INTEGER,dest_account_id INTEGER);
  CREATE TABLE IF NOT EXISTS ledger_entries(id INTEGER PRIMARY KEY AUTOINCREMENT,account_id INTEGER,transaction_id INTEGER,delta_cents INTEGER,balance_after INTEGER);
  CREATE TABLE IF NOT EXISTS crafted_item_events(id INTEGER PRIMARY KEY AUTOINCREMENT,crafted_item_id INTEGER,character_id INTEGER,event_type TEXT,details_json TEXT,created_at TEXT DEFAULT(datetime('now')));""")
  c.execute("INSERT INTO crafted_items VALUES(1,10,'guitar','A','A',100)");c.execute("INSERT INTO crafted_items VALUES(2,20,'bass','B','B',100)")
  c.execute("INSERT INTO band_members VALUES(1,10,'guitar')");c.execute("INSERT INTO band_members VALUES(1,20,'bass')")
  c.execute("INSERT INTO character_equipped_crafted_instruments(character_id,crafted_item_id) VALUES(10,1)");c.execute("INSERT INTO character_equipped_crafted_instruments(character_id,crafted_item_id) VALUES(20,2)")
  c.execute("INSERT INTO accounts(user_id,currency,balance_cents) VALUES(10,'USD',10000)")
 return s,p

def test_wear_only_applies_to_participants(tmp_path):
 s,p=setup(tmp_path);assert s.wear_band(1,2,[10])==1
 with sqlite3.connect(p) as c:
  assert c.execute("SELECT condition_percent FROM crafted_items WHERE id=1").fetchone()[0]==98
  assert c.execute("SELECT condition_percent FROM crafted_items WHERE id=2").fetchone()[0]==100

def test_maintenance_charges_exact_restored_condition(tmp_path):
 s,p=setup(tmp_path)
 with sqlite3.connect(p) as c:c.execute("UPDATE crafted_items SET condition_percent=90 WHERE id=1")
 item=s.repair(10,1,25);assert item["condition_percent"]==100
 with sqlite3.connect(p) as c:
  assert c.execute("SELECT balance_cents FROM accounts WHERE user_id=10").fetchone()[0]==8000
  assert c.execute("SELECT amount_cents FROM transactions WHERE type='luthiery_maintenance'").fetchone()[0]==2000

def test_maintenance_does_not_change_condition_when_unaffordable(tmp_path):
 s,p=setup(tmp_path)
 with sqlite3.connect(p) as c:c.execute("UPDATE crafted_items SET condition_percent=50 WHERE id=1");c.execute("UPDATE accounts SET balance_cents=0 WHERE user_id=10")
 with pytest.raises(ValueError,match="Insufficient funds"):s.repair(10,1,25)
 with sqlite3.connect(p) as c:assert c.execute("SELECT condition_percent FROM crafted_items WHERE id=1").fetchone()[0]==50
