import sqlite3
from services.luthiery_reputation_service import LuthieryReputationService

def test_sale_reputation_rewards_quality_and_diminishes_repeat_buyer(tmp_path):
 p=str(tmp_path/"rep.db");svc=LuthieryReputationService(p);svc.ensure_schema()
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,creator_character_id INTEGER,quality_score REAL)")
  c.execute("INSERT INTO crafted_items VALUES(1,10,90)")
  first=svc.award_sale(c,1,20,50000)
  svc.award_sale(c,1,20,50000);svc.award_sale(c,1,20,50000)
  fourth=svc.award_sale(c,1,20,50000)
 assert first==4 and fourth==2
 assert svc.profile(10)["reputation"]==14
 assert svc.item_history(1)[0]["character_id"]==20

def test_sale_reputation_always_credits_original_maker(tmp_path):
 p=str(tmp_path/"rep.db");svc=LuthieryReputationService(p);svc.ensure_schema()
 with sqlite3.connect(p) as c:
  c.execute("CREATE TABLE crafted_items(id INTEGER PRIMARY KEY,creator_character_id INTEGER,quality_score REAL)")
  c.execute("INSERT INTO crafted_items VALUES(9,99,75)")
  assert svc.award_sale(c,9,55,10000)==3
 assert svc.profile(99)["reputation"]==3
 assert svc.profile(55)["reputation"]==0
