import sqlite3
from services.luthiery_reputation_service import LuthieryReputationService

def test_famous_owner_is_one_time_and_boosts_desirability(tmp_path):
 p=str(tmp_path/"rep.db");s=LuthieryReputationService(p);s.ensure_schema()
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,creator_character_id INTEGER,quality_score REAL)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,80)")
 before=s.desirability(1)["score"]
 assert s.record_famous_owner(1,20,1500)==5
 assert s.record_famous_owner(1,20,1500)==0
 assert s.desirability(1)["score"]>before
 assert len([x for x in s.item_history(1) if x["event_type"]=="famous_owner"])==1
