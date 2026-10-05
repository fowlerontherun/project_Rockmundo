"""Safe consumer bridge for persistent crafted-instrument gameplay modifiers.

Phase 5 defines effects. Phase 7 will provide authoritative equipped item ids.
This service never treats every owned instrument as equipped.
"""
from __future__ import annotations
import json
import sqlite3
from services.luthiery_catalogue_service import DB_PATH
from services.crafted_instrument_equipment_service import CraftedInstrumentEquipmentService

CONTEXT_KEYS={
 "rehearsal":("practice_effectiveness","instrument_effectiveness"),
 "performance":("performance_quality","stage_presence","audience_reaction"),
 "recording":("recording_quality","instrument_effectiveness"),
}
MAX_CONTEXT_BONUS={"rehearsal":0.10,"performance":0.12,"recording":0.10}

class CraftedInstrumentEffectsService:
    def __init__(self,db_path:str|None=None): self.db_path=str(db_path or DB_PATH)

    def item_effects(self,character_id:int,item_id:int,context:str)->float:
        if context not in CONTEXT_KEYS: return 0.0
        try:
            with sqlite3.connect(self.db_path) as conn:
                row=conn.execute(
                  "SELECT stat_modifiers_json,condition_percent FROM crafted_items WHERE id=? AND owner_character_id=?",
                  (item_id,character_id)).fetchone()
        except sqlite3.OperationalError:
            return 0.0
        if not row: return 0.0
        try:\n            mods=json.loads(row[0] or "{}")\n            if not isinstance(mods,dict): return 0.0\n        except (json.JSONDecodeError,TypeError,ValueError):\n            return 0.0
        try: condition=max(0,min(100,int(row[1])))/100\n        except (TypeError,ValueError): return 0.0
        value=sum(max(-0.10,min(0.10,float(mods.get(k,0)))) for k in CONTEXT_KEYS[context])
        return round(max(-MAX_CONTEXT_BONUS[context],min(MAX_CONTEXT_BONUS[context],value*condition)),4)

    def band_effects(self,band_id:int,context:str)->float:
        equipment=CraftedInstrumentEquipmentService(self.db_path).band_equipment(band_id)
        return self.equipped_effects(equipment,context)

    def equipped_effects(self,character_items:dict[int,int],context:str)->float:
        """Aggregate explicit equipped item ids only; max one instrument per character."""
        total=sum(self.item_effects(cid,iid,context) for cid,iid in character_items.items())
        return round(max(-MAX_CONTEXT_BONUS.get(context,0),min(MAX_CONTEXT_BONUS.get(context,0),total)),4)

crafted_instrument_effects=CraftedInstrumentEffectsService()
