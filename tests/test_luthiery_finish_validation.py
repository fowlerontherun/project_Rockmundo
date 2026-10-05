import json, sqlite3, pytest
from services.luthiery_crafting_service import LuthieryCraftingService

def test_finish_metadata_is_validated_before_database_access(tmp_path):
 s=LuthieryCraftingService(str(tmp_path/"craft.db"))
 with pytest.raises(ValueError,match="Unsupported instrument finish"):
  s.craft(1,"x","X","guitar","shape",{},{"luthiery":100,"instrument_finishing":100},finish_key="evil")
 with pytest.raises(ValueError,match="Unsupported surface sheen"):
  s.craft(1,"x","X","guitar","shape",{},{"luthiery":100,"instrument_finishing":100},surface_sheen="mirror")

def test_advanced_finish_gate_is_server_authoritative(tmp_path):
 s=LuthieryCraftingService(str(tmp_path/"craft.db"))
 selections={p:{"material_key":"x"} for p in ("body","neck","fretboard","electronics","hardware")}
 with pytest.raises(ValueError,match="Instrument Finishing level 40"):
  s.craft(1,"x","X","guitar","shape",selections,{"luthiery":100,"instrument_finishing":39},finish_key="luthier.finish.metallic")
