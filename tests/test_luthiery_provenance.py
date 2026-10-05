import json,sqlite3,pytest
from services.luthiery_crafting_service import LuthieryCraftingService

def setup(tmp_path):
 p=str(tmp_path/"detail.db");s=LuthieryCraftingService(p);s.ensure_schema()
 with sqlite3.connect(p) as c:
  c.execute("INSERT OR IGNORE INTO instrument_shapes(key,name,instrument_type,required_skill,required_level,enabled) VALUES('shape','Shape','guitar','luthiery',1,1)")
  c.execute("""INSERT INTO crafted_items(id,serial_number,creator_character_id,owner_character_id,instrument_type,shape_key,name,quality_score,quality_tier)
   VALUES(1,'RM-X',10,10,'guitar','shape','Test',80,'Professional')""")
 return s

def test_detail_and_lock_are_character_safe(tmp_path):
 s=setup(tmp_path)
 assert s.detail(10,1)["serial_number"]=="RM-X"
 with pytest.raises(ValueError):s.detail(99,1)
 assert s.set_locked(10,1,True)["locked"]==1
 with pytest.raises(ValueError):s.set_locked(99,1,False)
 assert s.detail(10,1)["locked"]==1
