from routes import luthiery_routes

def test_authoritative_crafting_skills_are_character_scoped(monkeypatch):
 seen=[]
 def fake(character_id,skill):
  seen.append((character_id,skill.name));return {"luthiery":7,"woodworking":8,"fretwork":9,"instrument_electronics":10,"instrument_finishing":11}[skill.name]
 monkeypatch.setattr(luthiery_routes._skill_service,"get_skill_level",fake)
 skills=luthiery_routes._authoritative_crafting_skills(321)
 assert skills=={"luthiery":7,"woodworking":8,"fretwork":9,"instrument_electronics":10,"instrument_finishing":11}
 assert all(character_id==321 for character_id,_ in seen)
