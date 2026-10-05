import sqlite3
from services.luthiery_reputation_service import LuthieryReputationService

def test_notable_use_is_idempotent_and_increases_collectibility(tmp_path):
 p=str(tmp_path/"rep.db");svc=LuthieryReputationService(p);svc.ensure_schema()
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,creator_character_id INTEGER,quality_score REAL)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,95)")
 before=svc.desirability(1)["score"]
 first=svc.record_notable_use(1,"notable_gig",77,20,1500,{"venue":"Arena"})
 second=svc.record_notable_use(1,"notable_gig",77,20,1500,{"venue":"Arena"})
 after=svc.desirability(1)
 assert first>0 and second==0
 assert after["score"]>before
 assert len([x for x in svc.item_history(1) if x["event_type"]=="notable_gig"])==1
