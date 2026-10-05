import sqlite3,json
from services.luthiery_reputation_service import LuthieryReputationService

def test_masterpiece_and_signature_achievements_are_one_time(tmp_path):
 p=str(tmp_path/"rep.db");s=LuthieryReputationService(p);s.ensure_schema()
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,creator_character_id INTEGER,quality_score REAL)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,96)")
  for eid in (1,2,3):
   c.execute("INSERT INTO crafted_item_notable_history(crafted_item_id,event_type,character_id,details_json) VALUES(1,'notable_gig',20,?)",(json.dumps({"event_id":eid}),))
 first=s.evaluate_achievements(10);second=s.evaluate_achievements(10)
 keys={x["key"] for x in first}
 assert {"first_build","masterpiece","signature_instrument"}<=keys
 assert second==[]
 assert len(s.achievements(10))==3
