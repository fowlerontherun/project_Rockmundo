import sqlite3
import pytest
from services.luthiery_crafting_service import LuthieryCraftingService

def setup(db):
    svc=LuthieryCraftingService(db); svc.ensure_schema()
    with sqlite3.connect(db) as c:
        mids={r[1]:r[0] for r in c.execute("SELECT id,key FROM crafting_materials")}
        for key in ["luthier.material.basswood","luthier.material.poplar"]:
            c.execute("INSERT INTO character_crafting_materials(character_id,material_id,quantity) VALUES (101,?,10)",(mids[key],))
    return svc

def choices(material="luthier.material.basswood"):
    return {p:{"material_key":material} for p in ("body","neck","fretboard","electronics","hardware")}

def test_craft_persists_five_parts_and_provenance(tmp_path):
    db=str(tmp_path/"craft.db"); svc=setup(db)
    item=svc.craft(101,"req-1","First Build","guitar","luthier.shape.guitar.double_cut",choices(),{"luthiery":1})
    assert item["creator_character_id"]==101 and item["owner_character_id"]==101
    assert item["serial_number"].startswith("RM-")
    with sqlite3.connect(db) as c:
        assert c.execute("SELECT COUNT(*) FROM crafted_item_parts WHERE crafted_item_id=?",(item["id"],)).fetchone()[0]==5
        assert c.execute("SELECT SUM(quantity) FROM character_crafting_materials WHERE character_id=101").fetchone()[0]==15

def test_duplicate_request_is_idempotent_and_does_not_consume_twice(tmp_path):
    db=str(tmp_path/"craft.db"); svc=setup(db)
    first=svc.craft(101,"same","Build","guitar","luthier.shape.guitar.double_cut",choices(),{"luthiery":1})
    second=svc.craft(101,"same","Build","guitar","luthier.shape.guitar.double_cut",choices(),{"luthiery":1})
    assert first["id"]==second["id"]
    with sqlite3.connect(db) as c:
        assert c.execute("SELECT COUNT(*) FROM crafted_items").fetchone()[0]==1
        assert c.execute("SELECT COUNT(*) FROM crafting_jobs").fetchone()[0]==1

def test_other_character_cannot_spend_materials(tmp_path):
    db=str(tmp_path/"craft.db"); svc=setup(db)
    with pytest.raises(ValueError, match="do not own"):
        svc.craft(202,"req","Stolen","guitar","luthier.shape.guitar.double_cut",choices(),{"luthiery":100})

def test_premium_material_cannot_bypass_low_skill(tmp_path):
    db=str(tmp_path/"craft.db"); svc=setup(db)
    with sqlite3.connect(db) as c:
        mid=c.execute("SELECT id FROM crafting_materials WHERE key='luthier.material.premium_exotic'").fetchone()[0]
        c.execute("INSERT INTO character_crafting_materials(character_id,material_id,quantity) VALUES (101,?,5)",(mid,))
    with pytest.raises(ValueError, match="locked"):
        svc.craft(101,"premium","Premium","guitar","luthier.shape.guitar.double_cut",choices("luthier.material.premium_exotic"),{"luthiery":1})
