"""Persistent server-authoritative Luthiery live balance controls."""
import json,sqlite3
from services.luthiery_catalogue_service import DB_PATH
DEFAULT_WEIGHTS={"skill":.35,"materials":.35,"specialist":.15,"workshop":.10,"variance":.05}
class LuthieryBalanceService:
 def __init__(self,db_path=None):self.db_path=str(db_path or DB_PATH)
 def ensure_schema(self):
  with sqlite3.connect(self.db_path) as c:c.executescript("""CREATE TABLE IF NOT EXISTS luthiery_live_config(key TEXT PRIMARY KEY,value_json TEXT NOT NULL,updated_at TEXT NOT NULL DEFAULT(datetime('now')));
   CREATE TABLE IF NOT EXISTS luthiery_trait_controls(trait_key TEXT PRIMARY KEY,enabled INTEGER NOT NULL DEFAULT 1);""")
 def snapshot(self):
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   rows={r[0]:json.loads(r[1]) for r in c.execute("SELECT key,value_json FROM luthiery_live_config")}
  return {"quality_weights":rows.get("quality_weights",dict(DEFAULT_WEIGHTS)),
   "features":{k:bool(rows.get(f"feature:{k}",False)) for k in ("legendary_shapes","premium_materials","boutique_electronics","metallic_finishes")}}
 def quality_weights(self):
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   r=c.execute("SELECT value_json FROM luthiery_live_config WHERE key='quality_weights'").fetchone()
   return json.loads(r[0]) if r else dict(DEFAULT_WEIGHTS)
 def set_quality_weights(self,v):
  required=set(DEFAULT_WEIGHTS)
  if set(v)!=required or any(float(x)<0 for x in v.values()) or abs(sum(float(x) for x in v.values())-1)>0.0001:raise ValueError("Quality weights must contain the five weights, be non-negative and total 1.0")
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:c.execute("INSERT INTO luthiery_live_config(key,value_json,updated_at) VALUES('quality_weights',?,datetime('now')) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at",(json.dumps(v,sort_keys=True),))
  return v
 def feature_enabled(self,key):
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   r=c.execute("SELECT value_json FROM luthiery_live_config WHERE key=?",(f"feature:{key}",)).fetchone()
   return False if not r else bool(json.loads(r[0]))
 def set_feature(self,key,enabled):
  if key not in {"legendary_shapes","premium_materials","boutique_electronics","metallic_finishes"}:raise ValueError("Unsupported advanced feature")
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:c.execute("INSERT INTO luthiery_live_config(key,value_json,updated_at) VALUES(?,?,datetime('now')) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at",(f"feature:{key}",json.dumps(bool(enabled))))
  return {"feature":key,"enabled":bool(enabled)}
 def trait_enabled(self,key):
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:
   r=c.execute("SELECT enabled FROM luthiery_trait_controls WHERE trait_key=?",(key,)).fetchone();return True if not r else bool(r[0])
 def set_trait(self,key,enabled):
  self.ensure_schema()
  with sqlite3.connect(self.db_path) as c:c.execute("INSERT INTO luthiery_trait_controls(trait_key,enabled) VALUES(?,?) ON CONFLICT(trait_key) DO UPDATE SET enabled=excluded.enabled",(key,1 if enabled else 0))
balance_service=LuthieryBalanceService()
